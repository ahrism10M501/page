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
posts.json + graph.json + tags_registry.json 한 번에 업데이트.

Usage:
  uv run python post_update.py               # 증분 업데이트
  uv run python post_update.py --force       # 캐시 무시, 전체 임베딩 재계산
  uv run python post_update.py --posts-only  # posts.json만 업데이트 (그래프 스킵)
  uv run python post_update.py --suggest     # 태그 추천 표시
"""

import argparse

from posts_list_update import scan_posts, update_posts_json
from build_graph import update_graph
from auto_tag import init_registry, suggest_tags, load_registry


def main():
    parser = argparse.ArgumentParser(description="posts.json + graph.json + tags 자동 업데이트")
    parser.add_argument("--force", action="store_true", help="캐시 무시, 전체 임베딩 재계산")
    parser.add_argument("--posts-only", action="store_true", help="posts.json만 업데이트 (그래프 스킵)")
    parser.add_argument("--suggest", action="store_true", help="태그 추천 표시")
    args = parser.parse_args()

    print("포스트 스캔 중...")
    posts = scan_posts()
    print(f"  {len(posts)}개 포스트 발견: {[p['slug'] for p in posts]}")

    if not args.posts_only:
        print("\n태그 레지스트리 업데이트 중...")
        registry = init_registry(posts)

        # 태그가 비어 있는 포스트에 자동 할당
        auto_tagged = []
        for post in posts:
            if not post.get("tags"):
                suggestions = suggest_tags(post, registry)
                if suggestions:
                    post["tags"] = [tag for tag, _ in suggestions]
                    auto_tagged.append(post["slug"])

        if auto_tagged:
            print(f"태그 자동 할당: {auto_tagged}")

        if args.suggest:
            from auto_tag import normalize_tag
            print("\n=== 태그 추천 ===")
            for post in posts:
                suggestions = suggest_tags(post, registry)
                current = [normalize_tag(t) for t in post.get("tags", [])]
                new_tags = [(t, s) for t, s in suggestions if t not in current]
                if new_tags:
                    print(f"  [{post['slug']}] 추천: {[t for t, _ in new_tags]}")

    changed = update_posts_json(posts)
    print("posts.json 업데이트됨" if changed else "posts.json 변경 없음")

    if not args.posts_only:
        update_graph(posts, force=args.force)


if __name__ == "__main__":
    main()
