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
자동 태그 시스템.

- 포스트 임베딩 vs 태그 임베딩 비교로 태그 추천
- 매칭 부족 시 TF-IDF 키워드에서 새 태그 생성
- API 없이 로컬 임베딩만 사용

Usage:
  uv run python auto_tag.py init                # tags.json + 태그 임베딩 초기화
  uv run python auto_tag.py suggest <slug>       # 특정 포스트 태그 추천
  uv run python auto_tag.py suggest --all        # 전체 포스트 태그 추천
"""

import json
from pathlib import Path

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parent.parent
TAGS_PATH = ROOT / "blog" / "tags.json"
TAG_CACHE_PATH = ROOT / "blog" / ".tag_cache.json"

MATCH_THRESHOLD = 0.4
NEW_TAG_DEDUP_THRESHOLD = 0.8
MAX_TAGS = 5
MIN_TAGS = 2


def normalize_tag(tag: str) -> str:
    return tag.strip().lower().replace(" ", "-").replace("_", "-")


def load_tags(path: Path = TAGS_PATH) -> list[str]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def save_tags(tags: list[str], path: Path = TAGS_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(sorted(set(tags)), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_tag_cache(path: Path = TAG_CACHE_PATH) -> dict[str, list[float]]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_tag_cache(cache: dict[str, list[float]], path: Path = TAG_CACHE_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(cache, ensure_ascii=False),
        encoding="utf-8",
    )


def compute_tag_embeddings(
    posts: list[dict],
    post_embeddings: dict[str, np.ndarray],
) -> dict[str, np.ndarray]:
    """각 태그의 임베딩을 해당 태그를 가진 포스트 임베딩의 centroid로 계산."""
    tag_vectors: dict[str, list[np.ndarray]] = {}
    for post in posts:
        slug = post["slug"]
        if slug not in post_embeddings:
            continue
        emb = post_embeddings[slug]
        for tag in post.get("tags", []):
            canonical = normalize_tag(tag)
            tag_vectors.setdefault(canonical, []).append(emb)

    return {
        tag: np.mean(vectors, axis=0)
        for tag, vectors in tag_vectors.items()
    }


def recommend_tags(
    post_emb: np.ndarray,
    tag_cache: dict[str, np.ndarray],
    threshold: float = MATCH_THRESHOLD,
    max_tags: int = MAX_TAGS,
) -> list[tuple[str, float]]:
    """포스트 임베딩과 태그 임베딩의 cosine similarity로 태그 추천.

    Returns: [(tag, similarity), ...] 유사도 내림차순
    """
    if not tag_cache:
        return []

    tag_names = list(tag_cache.keys())
    tag_embs = np.array([tag_cache[t] for t in tag_names])
    sims = cosine_similarity([post_emb], tag_embs)[0]

    ranked = sorted(zip(tag_names, sims), key=lambda x: x[1], reverse=True)
    return [(t, float(s)) for t, s in ranked if s >= threshold][:max_tags]


def generate_new_tags(
    tfidf_keywords: list[str],
    existing_cache: dict[str, np.ndarray],
    max_new: int = 3,
) -> list[str]:
    """TF-IDF 키워드에서 새 태그 후보 생성.

    기존 태그와 이름이 같으면 제외.
    """
    existing_names = set(existing_cache.keys())
    candidates = []
    for kw in tfidf_keywords:
        normalized = normalize_tag(kw)
        if normalized and normalized not in existing_names and len(normalized) >= 2:
            candidates.append(normalized)
        if len(candidates) >= max_new:
            break
    return candidates


def assign_tags(
    post_emb: np.ndarray,
    tag_cache: dict[str, np.ndarray],
    tfidf_keywords: list[str],
    threshold: float = MATCH_THRESHOLD,
    max_tags: int = MAX_TAGS,
    min_tags: int = MIN_TAGS,
) -> list[str]:
    """포스트에 태그 할당: 추천 우선, 부족하면 생성."""
    recommended = recommend_tags(post_emb, tag_cache, threshold, max_tags)
    tags = [t for t, _ in recommended]

    if len(tags) < min_tags:
        new_tags = generate_new_tags(tfidf_keywords, tag_cache, max_new=min_tags - len(tags))
        tags.extend(new_tags)

    return tags[:max_tags]


def get_post_embeddings(posts: list[dict]) -> dict[str, np.ndarray]:
    """build_graph.py의 .post_cache.json에서 포스트 임베딩 로드.

    주의: update_graph()가 이미 실행되어 캐시가 최신 상태여야 한다.
    캐시에 없는 포스트만 스킵한다.
    """
    from build_graph import load_cache

    cache = load_cache()
    result = {}
    for p in posts:
        if p["slug"] in cache:
            result[p["slug"]] = np.array(cache[p["slug"]]["embedding"])
    return result


def init_tags(posts: list[dict]) -> tuple[list[str], dict[str, np.ndarray]]:
    """기존 포스트에서 태그 목록 + 태그 임베딩 초기화."""
    post_embs = get_post_embeddings(posts)
    tag_embs = compute_tag_embeddings(posts, post_embs)

    tags = sorted(tag_embs.keys())
    save_tags(tags)
    save_tag_cache({t: e.tolist() for t, e in tag_embs.items()})

    print(f"tags.json: {len(tags)}개 태그")
    print(f".tag_cache.json: 임베딩 저장 완료")
    return tags, tag_embs
