"""
Single source of truth for all constants and filesystem paths.
All paths are resolved relative to PROJECT_ROOT at import time — cwd-independent.
Override MODEL_NAME via PIPELINE_MODEL env var for testing.
"""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

POSTS_DIR: Path = PROJECT_ROOT / "posts"
BLOG_DIR: Path = PROJECT_ROOT / "blog"

POSTS_JSON: Path = BLOG_DIR / "posts.json"
GRAPH_JSON: Path = BLOG_DIR / "graph.json"
TAGS_JSON: Path = BLOG_DIR / "tags.json"

POST_CACHE: Path = BLOG_DIR / ".post_cache.json"
TAG_CACHE: Path = BLOG_DIR / ".tag_cache.json"

VOCAB_PATH: Path = PROJECT_ROOT / "pipeline" / "tag_vocabulary.json"

MODEL_NAME: str = os.environ.get("PIPELINE_MODEL", "jhgan/ko-sroberta-multitask")

# Graph construction
SIMILARITY_THRESHOLD: float = 0.3
MAX_EDGES_PER_NODE: int = 8
TFIDF_TOP_N: int = 20

# Tag assignment
MATCH_THRESHOLD: float = 0.4
NEW_TAG_DEDUP_THRESHOLD: float = 0.8
MAX_TAGS: int = 5
MIN_TAGS: int = 2

# Supernode clustering
MIN_POSTS_FOR_SUPERNODES: int = 30
SUPERNODE_DISTANCE_THRESHOLD: float = 0.5
