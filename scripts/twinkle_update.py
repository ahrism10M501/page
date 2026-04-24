#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pyyaml",
# ]
# ///
"""
twinkle/*.md 파일을 스캔해 twinkle/twinkles.json을 생성한다.

Usage:
  uv run python twinkle_update.py
"""

import json
import sys
from datetime import date
from pathlib import Path

from posts_list_update import parse_frontmatter_text

ROOT = Path(__file__).resolve().parent.parent
TWINKLE_DIR = ROOT / "twinkle"
TWINKLES_JSON = TWINKLE_DIR / "twinkles.json"


def scan_twinkles() -> list[dict]:
    """twinkle/*.md 스캔 → 메타데이터 + 본문 목록 (날짜 내림차순)."""
    twinkles = []
    for path in sorted(TWINKLE_DIR.glob("*.md")):
        fm, body = parse_frontmatter_text(path.read_text(encoding="utf-8"))
        if not fm.get("title"):
            print(f"  [SKIP] {path.name}: frontmatter에 title 없음", file=sys.stderr)
            continue
        twinkles.append({
            "slug": path.stem,
            "date": str(fm.get("date", date.today())),
            "title": str(fm["title"]),
            "tags": [str(t) for t in fm.get("tags", [])],
            "content": body.strip(),
        })
    twinkles.sort(key=lambda t: t["date"], reverse=True)
    return twinkles


def update_twinkles_json(twinkles: list[dict] | None = None) -> bool:
    """twinkles.json 생성/업데이트. 변경이 있으면 True 반환."""
    if twinkles is None:
        twinkles = scan_twinkles()
    new_text = json.dumps(twinkles, ensure_ascii=False, indent=2)
    old_text = TWINKLES_JSON.read_text(encoding="utf-8") if TWINKLES_JSON.exists() else ""
    if new_text == old_text:
        return False
    TWINKLES_JSON.write_text(new_text, encoding="utf-8")
    return True


def main():
    print("트윈클 스캔 중...")
    twinkles = scan_twinkles()
    print(f"  {len(twinkles)}개 트윈클 발견")
    changed = update_twinkles_json(twinkles)
    print("twinkles.json 업데이트됨" if changed else "twinkles.json 변경 없음")


if __name__ == "__main__":
    main()
