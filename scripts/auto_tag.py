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
자동 태그 시스템 — 태그 정규화 + 유사도 기반 태그 추천.

Usage:
  uv run python auto_tag.py init               # 기존 포스트에서 태그 레지스트리 초기화
  uv run python auto_tag.py suggest <slug>      # 특정 포스트에 태그 추천
  uv run python auto_tag.py suggest --all       # 전체 포스트 태그 추천
  uv run python auto_tag.py normalize           # 기존 포스트 태그를 정규화 형태로 변환
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "blog" / "tags_registry.json"
CACHE_FILE = ROOT / "blog" / ".post_cache.json"

MODEL_NAME = "jhgan/ko-sroberta-multitask"
TAG_THRESHOLD = 0.45
MAX_TAGS = 5
MIN_TAGS = 2


# ── 태그 정규화 ──────────────────────────────────────────────────────────────

def normalize_tag(tag: str) -> str:
    """태그를 정규 형태로 변환: 소문자 + 하이픈."""
    return tag.strip().lower().replace(" ", "-").replace("_", "-")


# ── 레지스트리 I/O ───────────────────────────────────────────────────────────

def load_registry() -> dict:
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {"tags": {}}


def save_registry(registry: dict):
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ── 임베딩 유틸 ──────────────────────────────────────────────────────────────

def _get_post_embeddings(posts: list[dict]) -> dict[str, np.ndarray]:
    """포스트 임베딩을 캐시에서 로드하거나 새로 계산."""
    from build_graph import compute_embeddings, get_post_text

    cache = {}
    if CACHE_FILE.exists():
        cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))

    texts = {p["slug"]: get_post_text(p) for p in posts}
    need = [p for p in posts if p["slug"] not in cache]

    if need:
        print(f"임베딩 계산: {[p['slug'] for p in need]}")
        embs = compute_embeddings([texts[p["slug"]] for p in need])
        for p, emb in zip(need, embs):
            cache[p["slug"]] = {
                "hash": "",
                "embedding": emb.tolist(),
            }

    return {p["slug"]: np.array(cache[p["slug"]]["embedding"]) for p in posts}


# ── 레지스트리 초기화 ────────────────────────────────────────────────────────

def init_registry(posts: list[dict]) -> dict:
    """기존 포스트의 태그를 스캔하여 레지스트리를 생성/갱신."""
    tag_post_indices: dict[str, list[int]] = {}
    alias_map: dict[str, set[str]] = {}

    for i, post in enumerate(posts):
        for tag in post.get("tags", []):
            canonical = normalize_tag(tag)
            tag_post_indices.setdefault(canonical, []).append(i)
            alias_map.setdefault(canonical, set()).add(tag)

    post_embs = _get_post_embeddings(posts)

    registry = {"tags": {}}
    for canonical, indices in tag_post_indices.items():
        embs = [post_embs[posts[i]["slug"]] for i in indices]
        centroid = np.mean(embs, axis=0)
        registry["tags"][canonical] = {
            "aliases": sorted(alias_map[canonical]),
            "embedding": centroid.tolist(),
        }

    save_registry(registry)
    print(f"레지스트리 저장: {len(registry['tags'])}개 태그 → {REGISTRY_PATH.relative_to(ROOT)}")
    return registry


# ── 태그 추천 ────────────────────────────────────────────────────────────────

def suggest_tags(
    post: dict,
    registry: dict,
    threshold: float = TAG_THRESHOLD,
    max_tags: int = MAX_TAGS,
    min_tags: int = MIN_TAGS,
) -> list[tuple[str, float]]:
    """포스트에 대해 기존 태그 유사도 기반 추천 목록 반환.

    Returns:
        [(canonical_tag, similarity), ...] 유사도 내림차순
    """
    if not registry["tags"]:
        return []

    from build_graph import compute_embeddings, get_post_text

    post_emb = compute_embeddings([get_post_text(post)])[0]

    tag_names = list(registry["tags"].keys())
    tag_embs = np.array([registry["tags"][t]["embedding"] for t in tag_names])

    sims = cosine_similarity([post_emb], tag_embs)[0]
    ranked = sorted(zip(tag_names, sims), key=lambda x: x[1], reverse=True)

    # threshold 이상인 태그 선택, 최소 min_tags 보장
    above = [(t, float(s)) for t, s in ranked if s >= threshold]
    if len(above) < min_tags:
        above = [(t, float(s)) for t, s in ranked[:min_tags]]

    return above[:max_tags]


def suggest_new_tags(post: dict) -> list[str]:
    """TF-IDF 키워드에서 새 태그 후보 추출."""
    from build_graph import extract_tfidf_keywords, get_post_text

    keywords = extract_tfidf_keywords([get_post_text(post)], top_n=5)
    if keywords:
        return list(keywords[0].keys())
    return []


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="자동 태그 시스템")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="기존 포스트에서 태그 레지스트리 초기화")

    sp_suggest = sub.add_parser("suggest", help="태그 추천")
    sp_suggest.add_argument("slug", nargs="?", help="포스트 slug (--all이면 생략)")
    sp_suggest.add_argument("--all", action="store_true", help="전체 포스트")

    sub.add_parser("normalize", help="기존 포스트 태그를 정규화 형태로 출력")

    args = parser.parse_args()

    from posts_list_update import scan_posts

    if args.command == "init":
        posts = scan_posts()
        print(f"{len(posts)}개 포스트 스캔 완료")
        init_registry(posts)

    elif args.command == "suggest":
        posts = scan_posts()
        registry = load_registry()
        if not registry["tags"]:
            print("레지스트리가 비어 있습니다. 먼저 'init'을 실행하세요.", file=sys.stderr)
            sys.exit(1)

        targets = posts if args.all else [p for p in posts if p["slug"] == args.slug]
        if not targets:
            print(f"포스트 '{args.slug}'를 찾을 수 없습니다.", file=sys.stderr)
            sys.exit(1)

        for post in targets:
            suggestions = suggest_tags(post, registry)
            current = [normalize_tag(t) for t in post.get("tags", [])]
            new_suggestions = [(t, s) for t, s in suggestions if t not in current]

            print(f"\n[{post['slug']}]")
            print(f"  현재 태그: {post.get('tags', [])}")
            print(f"  추천 태그:")
            for tag, sim in suggestions:
                marker = " ✓" if tag in current else " ★"
                print(f"    {marker} {tag} ({sim:.3f})")

            if new_suggestions:
                print(f"  새로 추가 추천: {[t for t, _ in new_suggestions]}")

    elif args.command == "normalize":
        posts = scan_posts()
        for post in posts:
            original = post.get("tags", [])
            normalized = [normalize_tag(t) for t in original]
            changed = original != normalized
            marker = " ← 변경" if changed else ""
            print(f"  [{post['slug']}] {original} → {normalized}{marker}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
