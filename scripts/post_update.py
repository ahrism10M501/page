#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pyyaml",
#   "sentence-transformers",
#   "scikit-learn",
#   "numpy",
# ]
# ///
"""
posts.json + graph.json 한 번에 업데이트.

Usage:
  uv run python post_update.py               # 증분 업데이트
  uv run python post_update.py --force       # 캐시 무시, 전체 임베딩 재계산
  uv run python post_update.py --posts-only  # posts.json만 업데이트 (그래프 스킵)
"""

import argparse

from posts_list_update import scan_posts, update_posts_json
from build_graph import update_graph


def main():
    parser = argparse.ArgumentParser(description="posts.json + graph.json 자동 업데이트")
    parser.add_argument("--force", action="store_true", help="캐시 무시, 전체 임베딩 재계산")
    parser.add_argument("--posts-only", action="store_true", help="posts.json만 업데이트 (그래프 스킵)")
    args = parser.parse_args()

    print("포스트 스캔 중...")
    posts = scan_posts()
    print(f"  {len(posts)}개 포스트 발견: {[p['slug'] for p in posts]}")

    changed = update_posts_json(posts)
    print("posts.json 업데이트됨" if changed else "posts.json 변경 없음")

    if not args.posts_only:
        update_graph(posts, force=args.force)


if __name__ == "__main__":
    main()
