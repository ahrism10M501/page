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
