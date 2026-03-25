"""
포스트 태그 추출 유틸리티

두 가지 방식으로 태그를 추출합니다:
1. extract_tags_from_md  : posts/ 디렉토리의 content.md 파일 직접 파싱
2. extract_tags_from_json: blog/posts.json에서 읽기
"""

import json
import re
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).parent
_DEFAULT_POSTS_DIR = _SCRIPTS_DIR.parent / "posts"
_DEFAULT_POSTS_JSON = _SCRIPTS_DIR.parent / "blog" / "posts.json"


def extract_tags_from_md(posts_dir: Path = _DEFAULT_POSTS_DIR) -> dict[str, list[str]]:
    """
    posts/<slug>/content.md의 YAML frontmatter에서 태그를 추출합니다.

    Args:
        posts_dir: posts 폴더 경로 (기본값: 이 스크립트 기준 ../posts)

    Returns:
        {slug: [tag, ...]} 형태의 딕셔너리
    """
    result = {}
    for md in sorted(Path(posts_dir).glob("*/content.md")):
        text = md.read_text(encoding="utf-8")
        match = re.search(r"^tags:\s*\[(.+?)\]", text, re.MULTILINE)
        if match:
            tags = [t.strip() for t in match.group(1).split(",")]
            result[md.parent.name] = tags
    return result


def extract_tags_from_json(posts_json: Path = _DEFAULT_POSTS_JSON) -> dict[str, list[str]]:
    """
    blog/posts.json에서 태그를 추출합니다.

    Args:
        posts_json: posts.json 파일 경로 (기본값: 이 스크립트 기준 ../blog/posts.json)

    Returns:
        {slug: [tag, ...]} 형태의 딕셔너리
    """
    posts = json.loads(Path(posts_json).read_text(encoding="utf-8"))
    return {p["slug"]: p.get("tags", []) for p in posts}


# ─── 사용법 ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # 1) content.md에서 직접 파싱
    print("=== content.md 파싱 ===")
    tags_md = extract_tags_from_md()
    for slug, tags in tags_md.items():
        print(f"  {slug}: {', '.join(tags)}")

    print()

    # 2) posts.json에서 읽기
    print("=== posts.json 읽기 ===")
    tags_json = extract_tags_from_json()
    for slug, tags in tags_json.items():
        print(f"  {slug}: {', '.join(tags)}")

    print()

    # 3) 전체 태그 목록 (중복 제거, 정렬)
    print("=== 전체 태그 목록 ===")
    all_tags = sorted({tag for tags in tags_json.values() for tag in tags})
    print(f"  {', '.join(all_tags)}")

    # 4) 태그별 포스트 역인덱스
    print()
    print("=== 태그별 포스트 ===")
    index: dict[str, list[str]] = {}
    for slug, tags in tags_json.items():
        for tag in tags:
            index.setdefault(tag, []).append(slug)
    for tag, slugs in sorted(index.items()):
        print(f"  [{tag}] {', '.join(slugs)}")
