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
