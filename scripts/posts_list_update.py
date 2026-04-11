#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pyyaml",
#   "nbformat",
# ]
# ///
"""
posts/ 디렉토리를 스캔해 posts.json을 업데이트한다.

content.ipynb가 있는 경우 content.md보다 우선한다.
ipynb의 첫 번째 마크다운 셀에서 YAML frontmatter를 파싱한다.

Usage:
  uv run python posts_list_update.py
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "posts"
POSTS_JSON = ROOT / "blog" / "posts.json"


def parse_frontmatter_text(text: str) -> tuple[dict, str]:
    """문자열에서 YAML frontmatter와 본문을 분리."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm = yaml.safe_load(text[3:end]) or {}
    body = text[end + 4:].lstrip("\n")
    return fm, body


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    """content.md에서 YAML frontmatter와 본문을 분리."""
    return parse_frontmatter_text(path.read_text(encoding="utf-8"))


def parse_notebook(path: Path) -> tuple[dict, str]:
    """content.ipynb의 첫 번째 마크다운 셀에서 frontmatter를 파싱하고
    전체 셀 텍스트를 본문으로 반환한다."""
    import nbformat
    nb = nbformat.read(str(path), as_version=4)

    fm: dict = {}
    body_parts: list[str] = []
    first = True

    for cell in nb.cells:
        source = cell.source.strip()
        if not source:
            continue
        if first and cell.cell_type == "markdown" and source.startswith("---"):
            fm, remaining = parse_frontmatter_text(source)
            if remaining.strip():
                body_parts.append(remaining.strip())
            first = False
            continue
        first = False
        if cell.cell_type == "markdown":
            body_parts.append(source)
        elif cell.cell_type == "code":
            body_parts.append(f"```python\n{source}\n```")

    return fm, "\n\n".join(body_parts)


def extract_summary(body: str, max_chars: int = 120) -> str:
    """본문 첫 번째 평문 단락에서 요약 자동 추출."""
    for line in body.splitlines():
        line = line.strip()
        if line and not line.startswith(("#", "```", "!", "|", "-", "*")):
            line = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line)
            line = re.sub(r'[`*_]', '', line)
            return line[:max_chars] + ("..." if len(line) > max_chars else "")
    return ""


def scan_posts() -> list[dict]:
    """posts/ 디렉토리를 스캔해 frontmatter 기반 포스트 목록 반환.

    content.ipynb가 있으면 content.md보다 우선한다.
    반환 dict의 _body, _path 키는 내부용이며 posts.json에 저장되지 않는다.
    """
    # slug → {"ipynb": Path, "md": Path} 수집
    sources: dict[str, dict] = {}
    for p in sorted(POSTS_DIR.glob("*/content.ipynb")):
        slug = p.parent.name
        if not slug.startswith("_"):
            sources.setdefault(slug, {})["ipynb"] = p
    for p in sorted(POSTS_DIR.glob("*/content.md")):
        slug = p.parent.name
        if not slug.startswith("_"):
            sources.setdefault(slug, {})["md"] = p

    posts = []
    for slug, paths in sorted(sources.items()):
        if "ipynb" in paths:
            fm, body = parse_notebook(paths["ipynb"])
            is_notebook = True
        else:
            fm, body = parse_frontmatter(paths["md"])
            is_notebook = False

        if not fm.get("title"):
            print(f"  [SKIP] {slug}: frontmatter에 title 없음", file=sys.stderr)
            continue

        post: dict = {
            "slug": slug,
            "title": str(fm["title"]),
            "date": str(fm.get("date", date.today())),
            "tags": [str(t) for t in fm.get("tags", [])],
            "summary": str(fm.get("summary") or extract_summary(body)),
            "_body": body,
            "_path": paths.get("ipynb") or paths.get("md"),
        }
        if is_notebook:
            post["notebook"] = True
        posts.append(post)

    return posts


def update_posts_json(posts: list[dict]) -> bool:
    """posts.json을 업데이트한다. 변경이 있으면 True를 반환한다.

    content.md / content.ipynb가 없는 기존 항목(수동 추가분)은 그대로 보존한다.
    """
    existing: dict[str, dict] = {}
    if POSTS_JSON.exists():
        for p in json.loads(POSTS_JSON.read_text(encoding="utf-8")):
            existing[p["slug"]] = p

    merged = dict(existing)
    for p in posts:
        merged[p["slug"]] = {k: v for k, v in p.items() if not k.startswith("_")}

    result = sorted(merged.values(), key=lambda p: p["date"], reverse=True)

    new_text = json.dumps(result, ensure_ascii=False, indent=2)
    old_text = POSTS_JSON.read_text(encoding="utf-8") if POSTS_JSON.exists() else ""
    if new_text == old_text:
        return False

    POSTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    POSTS_JSON.write_text(new_text, encoding="utf-8")
    return True


def main():
    print("포스트 스캔 중...")
    posts = scan_posts()
    print(f"  {len(posts)}개 포스트 발견: {[p['slug'] for p in posts]}")

    changed = update_posts_json(posts)
    print("posts.json 업데이트됨" if changed else "posts.json 변경 없음")


if __name__ == "__main__":
    main()
