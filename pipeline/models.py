"""
Shared data structures for the blog post update pipeline.
No imports from other pipeline modules.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict


class FrontMatter(TypedDict, total=False):
    title: str
    date: str
    tags: list[str]
    summary: str


class PostRecord(TypedDict, total=False):
    """
    Full post data passed between pipeline stages.
    Keys prefixed with '_' are internal and stripped before writing to posts.json.
    """
    slug: str
    title: str
    date: str
    tags: list[str]
    summary: str
    notebook: bool
    _body: str
    _path: str


class GraphNode(TypedDict):
    id: str
    title: str
    date: str
    tags: list[str]
    summary: str
    tfidf: dict[str, float]


class GraphEdge(TypedDict):
    source: str
    target: str
    weight: float


class SupernodeData(TypedDict):
    id: str
    label: str
    tags: list[str]


class _GraphDataRequired(TypedDict):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class GraphData(_GraphDataRequired, total=False):
    supernodes: list[SupernodeData]


class CacheEntry(TypedDict):
    hash: str
    embedding: list[float]


PostCache = dict[str, CacheEntry]
TagCache = dict[str, list[float]]
TfidfKeywords = dict[str, float]


@dataclass
class RunState:
    force: bool
    posts_only: bool
    stale_slugs: set[str] = field(default_factory=set)
    unchanged_slugs: set[str] = field(default_factory=set)
    tagless_slugs: set[str] = field(default_factory=set)
    new_tags_assigned: dict[str, list[str]] = field(default_factory=dict)
    posts_json_changed: bool = False
    graph_json_changed: bool = False
    tags_json_changed: bool = False
    errors: list[str] = field(default_factory=list)
