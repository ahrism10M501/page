import json
import pytest
from pathlib import Path


def make_md(tmp_path, name, fm_lines, body):
    p = tmp_path / name
    p.write_text(f"---\n{fm_lines}\n---\n{body}", encoding="utf-8")
    return p


def test_scan_twinkles_parses_frontmatter(monkeypatch, tmp_path):
    import twinkle_update
    monkeypatch.setattr(twinkle_update, "TWINKLE_DIR", tmp_path)
    make_md(tmp_path, "2026-04-24-test.md",
            "title: 테스트\ndate: 2026-04-24\ntags: [딥러닝]", "본문 내용")
    result = twinkle_update.scan_twinkles()
    assert len(result) == 1
    assert result[0]["slug"] == "2026-04-24-test"
    assert result[0]["title"] == "테스트"
    assert result[0]["date"] == "2026-04-24"
    assert result[0]["tags"] == ["딥러닝"]
    assert result[0]["content"] == "본문 내용"


def test_scan_twinkles_skips_no_title(monkeypatch, tmp_path):
    import twinkle_update
    monkeypatch.setattr(twinkle_update, "TWINKLE_DIR", tmp_path)
    make_md(tmp_path, "2026-04-24-notitle.md", "date: 2026-04-24", "내용")
    result = twinkle_update.scan_twinkles()
    assert result == []


def test_scan_twinkles_sorted_desc(monkeypatch, tmp_path):
    import twinkle_update
    monkeypatch.setattr(twinkle_update, "TWINKLE_DIR", tmp_path)
    make_md(tmp_path, "2026-04-20-older.md", "title: 오래된\ndate: 2026-04-20", "")
    make_md(tmp_path, "2026-04-24-newer.md", "title: 새로운\ndate: 2026-04-24", "")
    result = twinkle_update.scan_twinkles()
    assert result[0]["date"] == "2026-04-24"
    assert result[1]["date"] == "2026-04-20"


def test_scan_twinkles_ignores_subdirs(monkeypatch, tmp_path):
    import twinkle_update
    monkeypatch.setattr(twinkle_update, "TWINKLE_DIR", tmp_path)
    make_md(tmp_path, "2026-04-24-valid.md", "title: 유효\ndate: 2026-04-24", "")
    subdir = tmp_path / "images"
    subdir.mkdir()
    (subdir / "ignore.md").write_text("---\ntitle: 무시\ndate: 2026-04-24\n---\n", encoding="utf-8")
    result = twinkle_update.scan_twinkles()
    assert len(result) == 1


def test_update_twinkles_json_writes_file(monkeypatch, tmp_path):
    import twinkle_update
    monkeypatch.setattr(twinkle_update, "TWINKLES_JSON", tmp_path / "twinkles.json")
    twinkles = [{"slug": "a", "date": "2026-04-24", "title": "A", "tags": [], "content": "내용"}]
    changed = twinkle_update.update_twinkles_json(twinkles)
    assert changed is True
    data = json.loads((tmp_path / "twinkles.json").read_text())
    assert data[0]["slug"] == "a"


def test_update_twinkles_json_no_change(monkeypatch, tmp_path):
    import twinkle_update
    json_path = tmp_path / "twinkles.json"
    monkeypatch.setattr(twinkle_update, "TWINKLES_JSON", json_path)
    twinkles = [{"slug": "a", "date": "2026-04-24", "title": "A", "tags": [], "content": "내용"}]
    twinkle_update.update_twinkles_json(twinkles)
    changed = twinkle_update.update_twinkles_json(twinkles)
    assert changed is False


def test_scan_twinkles_missing_date_defaults_to_today(monkeypatch, tmp_path):
    from datetime import date
    import twinkle_update
    monkeypatch.setattr(twinkle_update, "TWINKLE_DIR", tmp_path)
    make_md(tmp_path, "2026-04-24-nodate.md", "title: 날짜없음", "내용")
    result = twinkle_update.scan_twinkles()
    assert len(result) == 1
    assert result[0]["date"] == str(date.today())
