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
