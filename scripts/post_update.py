#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pyyaml",
#   "nbformat",
#   "sentence-transformers",
#   "scikit-learn",
#   "numpy",
# ]
# ///
"""
posts.json + graph.json + tags.json 한 번에 업데이트.

Usage:
  uv run python post_update.py               # 증분 업데이트
  uv run python post_update.py --force       # 캐시 무시, 전체 임베딩 재계산
  uv run python post_update.py --posts-only  # posts.json만 업데이트 (그래프 스킵)
"""

import argparse

import numpy as np

from posts_list_update import scan_posts, update_posts_json
from build_graph import update_graph, extract_tfidf_keywords, get_post_text
from auto_tag import (
    init_tags, assign_tags, get_post_embeddings,
    load_tag_cache, normalize_tag, save_tags,
)
from twinkle_update import update_twinkles_json


def main():
    parser = argparse.ArgumentParser(description="posts.json + graph.json + tags 자동 업데이트")
    parser.add_argument("--force", action="store_true", help="캐시 무시, 전체 임베딩 재계산")
    parser.add_argument("--posts-only", action="store_true", help="posts.json만 업데이트 (그래프 스킵)")
    args = parser.parse_args()

    print("포스트 스캔 중...")
    posts = scan_posts()
    print(f"  {len(posts)}개 포스트 발견")

    if not args.posts_only:
        # 1) 임베딩 캐시 생성 (update_graph가 .post_cache.json을 채움)
        update_graph(posts, force=args.force)

        # 2) 태그가 있는 포스트로 태그 임베딩 초기화
        tagged_posts = [p for p in posts if p.get("tags")]
        if tagged_posts:
            known_tags, tag_embs = init_tags(tagged_posts)
        else:
            known_tags, tag_embs = [], {}

        # 3) 태그 없는 포스트에 자동 할당
        tagless = [p for p in posts if not p.get("tags")]
        if tagless:
            post_embs = get_post_embeddings(posts)
            tag_cache = {t: np.array(e) for t, e in load_tag_cache().items()}
            # TF-IDF는 전체 포스트 컨텍스트로 계산 (단일 문서 IDF 퇴화 방지)
            all_texts = [get_post_text(p) for p in posts]
            all_kw_lists = extract_tfidf_keywords(all_texts, top_n=10)
            tagless_indices = [i for i, p in enumerate(posts) if not p.get("tags")]

            new_tags_added = []
            for j, post in enumerate(tagless):
                slug = post["slug"]
                if slug not in post_embs:
                    print(f"  임베딩 없음, 스킵: [{slug}]")
                    continue
                kw = list(all_kw_lists[tagless_indices[j]].keys()) if tagless_indices[j] < len(all_kw_lists) else []
                # tag_cache는 이 루프에서 업데이트되지 않음:
                # generate_new_tags로 새 태그가 생성돼도 다음 포스트의 recommend_tags는 이를 볼 수 없음.
                # 새 태그 임베딩 계산은 다음 실행 시 init_tags에서 처리됨.
                post["tags"] = assign_tags(post_embs[slug], tag_cache, kw, post_text=all_texts[tagless_indices[j]])
                new_tags_added.extend(post["tags"])
                print(f"  태그 할당: [{slug}] → {post['tags']}")

            # 새로 생성된 태그를 tags.json에 추가
            if new_tags_added:
                all_tags = sorted(set(known_tags + new_tags_added))
                save_tags(all_tags)

        # 4) 모든 태그 정규화
        for post in posts:
            post["tags"] = [normalize_tag(t) for t in post.get("tags", [])]

    changed = update_posts_json(posts, force=args.force)
    print("posts.json 업데이트됨" if changed else "posts.json 변경 없음")

    if not args.posts_only:
        # 태그 반영된 posts로 graph.json 재생성
        update_graph(posts, force=False)

    # twinkle (ML 없음, 항상 실행)
    twinkle_changed = update_twinkles_json()
    print("twinkles.json 업데이트됨" if twinkle_changed else "twinkles.json 변경 없음")


if __name__ == "__main__":
    main()
