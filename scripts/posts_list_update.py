#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pyyaml",
# ]
# ///
"""
posts/ 디렉토리를 스캔해 posts.json을 업데이트한다.

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


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    """content.md에서 YAML frontmatter와 본문을 분리."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm = yaml.safe_load(text[3:end]) or {}
    body = text[end + 4:].lstrip("\n")
    return fm, body


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

    반환 dict의 _body, _path 키는 내부용이며 posts.json에 저장되지 않는다.
    """
    posts = []
    for md_path in sorted(POSTS_DIR.glob("*/content.md")):
        slug = md_path.parent.name
        if slug.startswith("_"):
            continue

        fm, body = parse_frontmatter(md_path)
        if not fm.get("title"):
            print(f"  [SKIP] {slug}: frontmatter에 title 없음", file=sys.stderr)
            continue

        posts.append({
            "slug": slug,
            "title": str(fm["title"]),
            "date": str(fm.get("date", date.today())),
            "tags": [str(t) for t in fm.get("tags", [])],
            "summary": str(fm.get("summary") or extract_summary(body)),
            "_body": body,
            "_path": md_path,
        })

    return posts


def update_posts_json(posts: list[dict]) -> bool:
    """posts.json을 업데이트한다. 변경이 있으면 True를 반환한다.

    content.md가 없는 기존 항목(수동 추가분)은 그대로 보존한다.
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
