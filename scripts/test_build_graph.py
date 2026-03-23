# scripts/test_build_graph.py
import json
import pytest

def test_compute_similarities_returns_symmetric_matrix():
    """임베딩 기반 유사도 행렬이 대칭이고 대각선이 1.0인지 확인"""
    from build_graph import compute_similarities
    import numpy as np

    # 간단한 임베딩 3개 (정규화된 벡터)
    embeddings = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.7071, 0.7071, 0.0],
    ])
    sim = compute_similarities(embeddings)
    assert sim.shape == (3, 3)
    # 대칭
    assert abs(sim[0][1] - sim[1][0]) < 1e-6
    # 대각선 ≈ 1.0
    for i in range(3):
        assert abs(sim[i][i] - 1.0) < 1e-6


def test_build_edges_respects_threshold_and_max():
    """threshold 미만 엣지 제거, 노드당 max_edges 제한 확인"""
    from build_graph import build_edges
    import numpy as np

    slugs = ["a", "b", "c", "d"]
    # a-b: 0.9, a-c: 0.5, a-d: 0.2 (threshold 미만)
    # b-c: 0.4, b-d: 0.35, c-d: 0.6
    sim = np.array([
        [1.0, 0.9, 0.5, 0.2],
        [0.9, 1.0, 0.4, 0.35],
        [0.5, 0.4, 1.0, 0.6],
        [0.2, 0.35, 0.6, 1.0],
    ])
    edges = build_edges(sim, slugs, threshold=0.3, max_edges_per_node=2)
    # a-d (0.2) 는 threshold 미만이므로 제외
    sources_targets = [(e["source"], e["target"]) for e in edges]
    assert ("a", "d") not in sources_targets
    assert ("d", "a") not in sources_targets
    # 각 노드의 엣지 수가 max_edges_per_node 이하
    from collections import Counter
    counts = Counter()
    for e in edges:
        counts[e["source"]] += 1
        counts[e["target"]] += 1
    for node, count in counts.items():
        assert count <= 2, f"Node {node} has {count} edges, max is 2"


def test_extract_tfidf_keywords():
    """TF-IDF 키워드 추출이 상위 N개를 반환하는지 확인"""
    from build_graph import extract_tfidf_keywords

    texts = [
        "머신러닝 딥러닝 인공지능 모델 학습",
        "웹 개발 프론트엔드 자바스크립트 리액트",
        "머신러닝 모델 학습 데이터 전처리",
    ]
    keywords_list = extract_tfidf_keywords(texts, top_n=3)
    assert len(keywords_list) == 3
    for kw in keywords_list:
        assert len(kw) <= 3
        # 각 키워드는 (단어, 점수) 형태의 dict
        for word, score in kw.items():
            assert isinstance(word, str)
            assert isinstance(score, float)
            assert score > 0
