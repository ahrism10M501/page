import json
import tempfile
from pathlib import Path

def test_normalize_tag():
    from auto_tag import normalize_tag
    assert normalize_tag("Deep-Learning") == "deep-learning"
    assert normalize_tag("DL") == "dl"
    assert normalize_tag("computer vision") == "computer-vision"
    assert normalize_tag("  PyTorch ") == "pytorch"
    assert normalize_tag("deep_learning") == "deep-learning"

def test_save_load_tags(tmp_path):
    from auto_tag import save_tags, load_tags
    path = tmp_path / "tags.json"
    save_tags(["python", "deep-learning", "docker"], path)
    assert load_tags(path) == ["deep-learning", "docker", "python"]  # save_tags가 정렬

def test_save_load_tag_cache(tmp_path):
    from auto_tag import save_tag_cache, load_tag_cache
    path = tmp_path / ".tag_cache.json"
    data = {"python": [0.1, 0.2], "docker": [0.3, 0.4]}
    save_tag_cache(data, path)
    loaded = load_tag_cache(path)
    assert list(loaded.keys()) == ["python", "docker"]

def test_compute_tag_embeddings():
    """태그 임베딩 = 해당 태그를 가진 포스트 임베딩의 centroid."""
    from auto_tag import compute_tag_embeddings
    import numpy as np

    post_embeddings = {
        "post-a": np.array([1.0, 0.0, 0.0]),
        "post-b": np.array([0.0, 1.0, 0.0]),
        "post-c": np.array([1.0, 1.0, 0.0]),
    }
    posts = [
        {"slug": "post-a", "tags": ["python", "ml"]},
        {"slug": "post-b", "tags": ["python", "docker"]},
        {"slug": "post-c", "tags": ["ml"]},
    ]
    result = compute_tag_embeddings(posts, post_embeddings)

    # python = mean(post-a, post-b) = [0.5, 0.5, 0.0]
    np.testing.assert_array_almost_equal(result["python"], [0.5, 0.5, 0.0])
    # ml = mean(post-a, post-c) = [1.0, 0.5, 0.0]
    np.testing.assert_array_almost_equal(result["ml"], [1.0, 0.5, 0.0])
    # docker = mean(post-b) = [0.0, 1.0, 0.0]
    np.testing.assert_array_almost_equal(result["docker"], [0.0, 1.0, 0.0])

def test_recommend_tags():
    """포스트 임베딩과 태그 임베딩의 cosine similarity로 추천."""
    from auto_tag import recommend_tags
    import numpy as np

    post_emb = np.array([1.0, 0.0, 0.0])
    tag_cache = {
        "ml": np.array([0.9, 0.1, 0.0]),         # 높은 유사도
        "docker": np.array([0.0, 0.0, 1.0]),      # 낮은 유사도
        "python": np.array([0.7, 0.3, 0.0]),      # 중간 유사도
    }
    result = recommend_tags(post_emb, tag_cache, threshold=0.4, max_tags=5)
    tags = [t for t, _ in result]
    assert "ml" in tags
    assert "python" in tags
    assert "docker" not in tags  # 유사도 낮아서 제외

    # Verify sorted descending by similarity
    assert tags[0] == "ml"  # highest similarity
    # Verify float values returned and ordered
    assert result[0][1] > result[1][1]

def test_recommend_tags_empty():
    from auto_tag import recommend_tags
    import numpy as np
    result = recommend_tags(np.array([1.0, 0.0]), {}, threshold=0.4, max_tags=5)
    assert result == []

def test_recommend_tags_max_tags():
    """max_tags limits results even when more tags exceed threshold."""
    from auto_tag import recommend_tags
    import numpy as np

    post_emb = np.array([1.0, 0.0])
    tag_cache = {
        "a": np.array([1.0, 0.0]),
        "b": np.array([0.9, 0.1]),
        "c": np.array([0.8, 0.2]),
        "d": np.array([0.7, 0.3]),
    }
    result = recommend_tags(post_emb, tag_cache, threshold=0.5, max_tags=2)
    assert len(result) == 2
    # First result should be "a" (highest similarity)
    assert result[0][0] == "a"

def test_generate_new_tags():
    """TF-IDF 키워드에서 새 태그 후보 생성, 기존 태그와 중복 제거."""
    from auto_tag import generate_new_tags
    import numpy as np

    # 기존 태그가 없으면 키워드가 그대로 태그가 됨
    keywords = ["신경망", "pytorch", "역전파"]
    existing_cache = {}
    result = generate_new_tags(keywords, existing_cache, max_new=2)
    assert len(result) <= 2
    assert all(isinstance(t, str) for t in result)

def test_generate_new_tags_dedup():
    """기존 태그와 이름이 겹치면 제외."""
    from auto_tag import generate_new_tags
    import numpy as np

    keywords = ["python", "새키워드"]
    existing_cache = {"python": np.array([0.1, 0.2])}
    result = generate_new_tags(keywords, existing_cache, max_new=3)
    assert "python" not in result

def test_assign_tags_with_existing():
    """기존 태그가 있으면 추천으로 채움."""
    from auto_tag import assign_tags
    import numpy as np

    post_emb = np.array([1.0, 0.0])
    tag_cache = {"deep-learning": np.array([0.9, 0.1])}

    result = assign_tags(post_emb, tag_cache, tfidf_keywords=[], min_tags=1)
    assert "deep-learning" in result

def test_assign_tags_fallback_to_generate():
    """추천이 부족하면 TF-IDF에서 새 태그 생성."""
    from auto_tag import assign_tags
    import numpy as np

    post_emb = np.array([1.0, 0.0])
    tag_cache = {"docker": np.array([0.0, 1.0])}  # 유사도 낮음

    result = assign_tags(post_emb, tag_cache, tfidf_keywords=["pytorch", "신경망"], min_tags=2)
    assert len(result) >= 2
