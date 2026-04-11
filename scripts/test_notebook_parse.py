#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pyyaml",
#   "nbformat",
# ]
# ///
"""posts_list_update.py의 ipynb 파싱 로직 단위 테스트."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from posts_list_update import parse_notebook, parse_frontmatter_text


def make_notebook(cells: list[dict]) -> dict:
    """최소한의 nbformat 4 노트북 dict 생성."""
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {"kernelspec": {"name": "python3"}},
        "cells": cells,
    }


def make_md_cell(source: str) -> dict:
    return {"cell_type": "markdown", "source": source, "metadata": {}}


def make_code_cell(source: str) -> dict:
    return {"cell_type": "code", "source": source, "metadata": {}, "outputs": [], "execution_count": None}


def test_parse_frontmatter_text_basic():
    text = "---\ntitle: Hello\ndate: 2026-01-01\n---\n본문"
    fm, body = parse_frontmatter_text(text)
    assert fm["title"] == "Hello", f"got {fm['title']}"
    assert str(fm["date"]) == "2026-01-01", f"got {fm['date']}"
    assert "본문" in body, f"got {body!r}"


def test_parse_frontmatter_text_no_frontmatter():
    text = "그냥 본문"
    fm, body = parse_frontmatter_text(text)
    assert fm == {}, f"got {fm}"
    assert body == "그냥 본문", f"got {body!r}"


def test_parse_notebook_with_frontmatter():
    nb = make_notebook([
        make_md_cell("---\ntitle: 테스트 노트북\ndate: 2026-04-11\ntags: [python]\n---\n소개 문단"),
        make_code_cell("x = 1 + 1\nprint(x)"),
        make_md_cell("## 결론"),
    ])
    with tempfile.NamedTemporaryFile(suffix=".ipynb", mode="w", delete=False, encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False)
        tmp = Path(f.name)
    fm, body = parse_notebook(tmp)
    tmp.unlink()

    assert fm["title"] == "테스트 노트북", f"got {fm.get('title')}"
    assert fm["tags"] == ["python"], f"got {fm.get('tags')}"
    assert "소개 문단" in body, f"body: {body!r}"
    assert "```python" in body, f"body: {body!r}"
    assert "x = 1 + 1" in body, f"body: {body!r}"
    assert "## 결론" in body, f"body: {body!r}"


def test_parse_notebook_without_frontmatter():
    nb = make_notebook([
        make_md_cell("# 제목 없는 노트북"),
        make_code_cell("print('hello')"),
    ])
    with tempfile.NamedTemporaryFile(suffix=".ipynb", mode="w", delete=False, encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False)
        tmp = Path(f.name)
    fm, body = parse_notebook(tmp)
    tmp.unlink()

    assert fm == {}, f"got {fm}"
    assert "# 제목 없는 노트북" in body, f"body: {body!r}"


def test_parse_notebook_empty_cells_skipped():
    nb = make_notebook([
        make_md_cell("---\ntitle: 빈 셀 테스트\n---"),
        make_md_cell(""),        # 빈 셀 — 무시
        make_code_cell("a = 1"),
    ])
    with tempfile.NamedTemporaryFile(suffix=".ipynb", mode="w", delete=False, encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False)
        tmp = Path(f.name)
    fm, body = parse_notebook(tmp)
    tmp.unlink()

    assert fm["title"] == "빈 셀 테스트", f"got {fm.get('title')}"
    assert "a = 1" in body, f"body: {body!r}"


if __name__ == "__main__":
    tests = [
        test_parse_frontmatter_text_basic,
        test_parse_frontmatter_text_no_frontmatter,
        test_parse_notebook_with_frontmatter,
        test_parse_notebook_without_frontmatter,
        test_parse_notebook_empty_cells_skipped,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(failed)
