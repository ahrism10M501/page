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
blog/graph.json을 생성하는 빌드 스크립트.

Usage:
  uv run python build_graph.py           # 증분 업데이트
  uv run python build_graph.py --force   # 캐시 무시, 전체 재계산
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


ROOT = Path(__file__).resolve().parent.parent
GRAPH_JSON = ROOT / "blog" / "graph.json"
CACHE_FILE = ROOT / "blog" / ".post_cache.json"

SIMILARITY_THRESHOLD = 0.3
MAX_EDGES_PER_NODE = 8
TFIDF_TOP_N = 20
MODEL_NAME = "jhgan/ko-sroberta-multitask"


# ── 캐시 ──────────────────────────────────────────────────────────────────────

def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def load_cache() -> dict:
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict):
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


# ── 텍스트 준비 ────────────────────────────────────────────────────────────────

def get_post_text(post: dict) -> str:
    """임베딩·TF-IDF에 사용할 텍스트 조합: 제목 + 요약 + 본문."""
    return "\n".join([post.get("title", ""), post.get("summary", ""), post.get("_body", "")])


# ── 임베딩 ────────────────────────────────────────────────────────────────────

def compute_embeddings(texts: list[str]) -> np.ndarray:
    """sentence-transformers로 텍스트 임베딩 생성."""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL_NAME)
    return model.encode(texts, show_progress_bar=True, convert_to_numpy=True)


def compute_similarities(embeddings: np.ndarray) -> np.ndarray:
    """cosine similarity 행렬 계산."""
    return cosine_similarity(embeddings)


# ── TF-IDF ────────────────────────────────────────────────────────────────────

def extract_tfidf_keywords(texts: list[str], top_n: int = TFIDF_TOP_N) -> list[dict]:
    """각 텍스트에서 TF-IDF 상위 키워드 추출."""
    try:
        from konlpy.tag import Mecab
        tokenizer = Mecab().morphs
    except Exception:
        tokenizer = str.split

    vec = TfidfVectorizer(tokenizer=tokenizer, max_features=5000)
    mat = vec.fit_transform(texts)
    names = vec.get_feature_names_out()

    result = []
    for i in range(mat.shape[0]):
        row = mat[i].toarray().flatten()
        top = row.argsort()[-top_n:][::-1]
        result.append({names[j]: round(float(row[j]), 4) for j in top if row[j] > 0})
    return result


# ── 엣지 ──────────────────────────────────────────────────────────────────────

def build_edges(
    sim_matrix: np.ndarray,
    slugs: list[str],
    threshold: float = SIMILARITY_THRESHOLD,
    max_edges_per_node: int = MAX_EDGES_PER_NODE,
) -> list[dict]:
    """유사도 행렬에서 엣지 목록 생성."""
    n = len(slugs)
    candidates = [
        (float(sim_matrix[i][j]), i, j)
        for i in range(n)
        for j in range(i + 1, n)
        if float(sim_matrix[i][j]) >= threshold
    ]
    candidates.sort(reverse=True)

    degree = [0] * n
    edges = []
    for w, i, j in candidates:
        if degree[i] < max_edges_per_node and degree[j] < max_edges_per_node:
            edges.append({"source": slugs[i], "target": slugs[j], "weight": round(w, 4)})
            degree[i] += 1
            degree[j] += 1
    return edges


# ── 메인 로직 ─────────────────────────────────────────────────────────────────

def update_graph(posts: list[dict], force: bool = False):
    """graph.json 업데이트 (증분 임베딩 캐시 사용).

    posts 각 항목은 scan_posts()가 반환한 dict로,
    _body 키에 본문 텍스트가 담겨 있어야 한다.
    """
    if not posts:
        GRAPH_JSON.write_text(
            json.dumps({"nodes": [], "edges": []}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print("포스트 없음. 빈 graph.json 생성.")
        return

    cache = {} if force else load_cache()
    texts = {p["slug"]: get_post_text(p) for p in posts}

    stale = [
        p for p in posts
        if p["slug"] not in cache
        or cache[p["slug"]]["hash"] != content_hash(texts[p["slug"]])
    ]

    if not stale:
        print("모든 임베딩 캐시 유효 — 모델 로딩 스킵.")
    else:
        print(f"임베딩 재계산: {[p['slug'] for p in stale]}")
        print("모델 로딩 중 (첫 실행 시 다운로드)...")
        new_embs = compute_embeddings([texts[p["slug"]] for p in stale])
        for p, emb in zip(stale, new_embs):
            cache[p["slug"]] = {
                "hash": content_hash(texts[p["slug"]]),
                "embedding": emb.tolist(),
            }
        save_cache(cache)
        print(f"캐시 저장 완료 → {CACHE_FILE.relative_to(ROOT)}")

    slugs = [p["slug"] for p in posts]
    embeddings = np.array([cache[slug]["embedding"] for slug in slugs])
    sim_matrix = compute_similarities(embeddings)

    print("TF-IDF 키워드 추출 중...")
    keywords_list = extract_tfidf_keywords([texts[slug] for slug in slugs])

    nodes = [
        {
            "id": p["slug"],
            "title": p["title"],
            "date": p["date"],
            "tags": p["tags"],
            "summary": p.get("summary", ""),
            "tfidf": keywords_list[i],
        }
        for i, p in enumerate(posts)
    ]
    edges = build_edges(sim_matrix, slugs)

    GRAPH_JSON.parent.mkdir(parents=True, exist_ok=True)
    GRAPH_JSON.write_text(
        json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"graph.json 생성 완료 ({len(nodes)} nodes, {len(edges)} edges)")


def main():
    parser = argparse.ArgumentParser(description="graph.json 업데이트")
    parser.add_argument("--force", action="store_true", help="캐시 무시, 전체 재계산")
    args = parser.parse_args()

    from posts_list_update import scan_posts
    print("포스트 스캔 중...")
    posts = scan_posts()
    print(f"  {len(posts)}개 포스트 발견")
    update_graph(posts, force=args.force)


if __name__ == "__main__":
    main()
