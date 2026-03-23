#!/usr/bin/env python3
"""blog/graph.json을 생성하는 빌드 스크립트.

Usage: cd scripts && uv run build_graph.py
"""

import json
import sys
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# --- 프로젝트 루트 경로 ---
ROOT = Path(__file__).resolve().parent.parent
POSTS_JSON = ROOT / "blog" / "posts.json"
POSTS_DIR = ROOT / "posts"
OUTPUT = ROOT / "blog" / "graph.json"

# --- 설정 ---
SIMILARITY_THRESHOLD = 0.3
MAX_EDGES_PER_NODE = 8
TFIDF_TOP_N = 20
MODEL_NAME = "jhgan/ko-sroberta-multitask"


def load_posts():
    """posts.json과 각 포스트의 content.md를 읽어 반환."""
    with open(POSTS_JSON, "r", encoding="utf-8") as f:
        posts = json.load(f)

    for post in posts:
        md_path = POSTS_DIR / post["slug"] / "content.md"
        if md_path.exists():
            post["content"] = md_path.read_text(encoding="utf-8")
        else:
            post["content"] = ""

    return posts


def get_post_text(post):
    """임베딩에 사용할 텍스트 조합: 제목 + 요약 + 본문."""
    parts = [post.get("title", ""), post.get("summary", ""), post.get("content", "")]
    return "\n".join(parts)


def compute_embeddings(texts):
    """sentence-transformers로 텍스트 임베딩 생성."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    return embeddings


def compute_similarities(embeddings):
    """cosine similarity 행렬 계산."""
    return cosine_similarity(embeddings)


def build_edges(sim_matrix, slugs, threshold=SIMILARITY_THRESHOLD, max_edges_per_node=MAX_EDGES_PER_NODE):
    """유사도 행렬에서 엣지 목록 생성. threshold 이상, 노드당 max_edges 제한."""
    n = len(slugs)

    # 모든 후보 엣지를 weight 내림차순으로 수집
    candidates = []
    for i in range(n):
        for j in range(i + 1, n):
            w = float(sim_matrix[i][j])
            if w >= threshold:
                candidates.append((w, i, j))
    candidates.sort(key=lambda x: x[0], reverse=True)

    # Greedy: 높은 weight 순으로 추가하되 양쪽 노드의 degree가 max_edges_per_node 미만일 때만
    degree = [0] * n
    selected = []
    for w, i, j in candidates:
        if degree[i] < max_edges_per_node and degree[j] < max_edges_per_node:
            selected.append((i, j, w))
            degree[i] += 1
            degree[j] += 1

    edges = []
    for i, j, w in selected:
        edges.append({
            "source": slugs[i],
            "target": slugs[j],
            "weight": round(w, 4),
        })

    return edges


def extract_tfidf_keywords(texts, top_n=TFIDF_TOP_N):
    """각 텍스트에서 TF-IDF 상위 키워드 추출. Mecab 토크나이저 사용."""
    try:
        from konlpy.tag import Mecab
        mecab = Mecab()
        tokenizer = mecab.morphs
    except Exception:
        # Mecab 불가 시 공백 분리 폴백
        tokenizer = str.split

    vectorizer = TfidfVectorizer(tokenizer=tokenizer, max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(texts)
    feature_names = vectorizer.get_feature_names_out()

    keywords_list = []
    for i in range(tfidf_matrix.shape[0]):
        row = tfidf_matrix[i].toarray().flatten()
        top_indices = row.argsort()[-top_n:][::-1]
        kw = {}
        for idx in top_indices:
            if row[idx] > 0:
                kw[feature_names[idx]] = round(float(row[idx]), 4)
        keywords_list.append(kw)

    return keywords_list


def build_graph_json(posts, sim_matrix, keywords_list):
    """최종 graph.json 구조 생성."""
    slugs = [p["slug"] for p in posts]
    edges = build_edges(sim_matrix, slugs)

    nodes = []
    for i, post in enumerate(posts):
        nodes.append({
            "id": post["slug"],
            "title": post["title"],
            "date": post["date"],
            "tags": post["tags"],
            "summary": post.get("summary", ""),
            "tfidf": keywords_list[i],
        })

    return {"nodes": nodes, "edges": edges}


def main():
    posts = load_posts()

    if not posts:
        OUTPUT.write_text(json.dumps({"nodes": [], "edges": []}, ensure_ascii=False, indent=2))
        print("No posts found. Empty graph.json written.")
        return

    texts = [get_post_text(p) for p in posts]

    print(f"Computing embeddings for {len(posts)} posts...")
    embeddings = compute_embeddings(texts)

    print("Computing similarities...")
    sim_matrix = compute_similarities(embeddings)

    print("Extracting TF-IDF keywords...")
    keywords_list = extract_tfidf_keywords(texts)

    graph = build_graph_json(posts, sim_matrix, keywords_list)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(graph, ensure_ascii=False, indent=2))
    print(f"graph.json written to {OUTPUT} ({len(graph['nodes'])} nodes, {len(graph['edges'])} edges)")


if __name__ == "__main__":
    main()
