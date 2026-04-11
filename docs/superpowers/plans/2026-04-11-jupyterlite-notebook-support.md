# JupyterLite Notebook Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `.ipynb` 파일을 `posts/<slug>/content.ipynb`에 넣으면 블로그 포스트로 자동 인식되고, 정적 미리보기와 JupyterLite 실행 환경이 제공된다.

**Architecture:**  
1. GitHub Actions가 push마다 JupyterLite를 빌드해 `/lab/`에 배포하고 전체 사이트를 Pages에 올린다.  
2. 빌드 파이프라인(`posts_list_update.py`)이 `content.ipynb`를 읽어 posts.json/graph.json/tags.json을 생성한다 (ipynb 우선).  
3. `post.js`가 `post.notebook === true`를 감지하면 셀을 정적 렌더링 + JupyterLite 링크를 삽입한다.

**Tech Stack:** nbformat, JupyterLite (jupyterlite-core + jupyterlite-pyodide-kernel), GitHub Actions, marked.js, highlight.js

---

## File Map

| 상태 | 파일 | 역할 |
|------|------|------|
| NEW | `.github/workflows/deploy.yml` | JupyterLite 빌드 + Pages 배포 |
| NEW | `.nojekyll` | Jekyll 비활성화 |
| MOD | `scripts/posts_list_update.py` | ipynb 파싱 추가 |
| NEW | `scripts/test_notebook_parse.py` | 파서 단위 테스트 |
| MOD | `post.js` | 노트북 정적 렌더링 + JupyterLite 버튼 |
| MOD | `style.css` | 노트북 셀 스타일 |
| NEW | `posts/Gaussian_ Z-score_Normalization/content.ipynb` | 샘플 노트북 포스트 |

---

## ⚠️ 수동 설정 (1회)

GitHub 리포 Settings → Pages → Source를 **"GitHub Actions"** 로 변경해야 한다.  
변경 전까지 Actions 워크플로우가 Pages에 배포되지 않는다.

---

## Task 1: `.nojekyll` + GitHub Actions 워크플로우

**Files:**
- Create: `.nojekyll`
- Create: `.github/workflows/deploy.yml`

- [ ] **Step 1: `.nojekyll` 파일 생성**

```bash
touch /home/ahris/ahrism-pages/.nojekyll
```

- [ ] **Step 2: `.github/workflows/deploy.yml` 작성**

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install JupyterLite
        run: pip install jupyterlite-core jupyterlite-pyodide-kernel

      - name: Collect notebooks for JupyterLite
        run: |
          mkdir -p _jl_contents
          for ipynb in posts/*/content.ipynb; do
            [ -f "$ipynb" ] || continue
            slug=$(basename $(dirname "$ipynb"))
            mkdir -p "_jl_contents/posts/$slug"
            cp "$ipynb" "_jl_contents/posts/$slug/content.ipynb"
          done

      - name: Build JupyterLite
        run: jupyter lite build --contents _jl_contents --output-dir lab

      - name: Prepare site
        run: |
          mkdir -p _site
          # Static site files
          cp -r index.html style.css app.js post.js graph.js sidebar.js page-fold.js \
                blog posts github projects.json github-sources.json .nojekyll _site/ 2>/dev/null || true
          # JupyterLite
          cp -r lab _site/

      - name: Upload Pages artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: '_site'

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/deploy-pages@v4
        id: deployment
```

- [ ] **Step 3: `.gitignore`에 lab/ 추가**

`.gitignore`에 다음 줄 추가:
```
# JupyterLite (CI에서 빌드됨)
lab/
_jl_contents/
_site/
```

- [ ] **Step 4: 커밋**

```bash
git add .nojekyll .github/workflows/deploy.yml .gitignore
git commit -m "ci: GitHub Actions로 JupyterLite 빌드 + Pages 배포"
```

---

## Task 2: `posts_list_update.py` — ipynb 파서 추가

**Files:**
- Modify: `scripts/posts_list_update.py`

- [ ] **Step 1: 파일 상단 의존성 선언에 nbformat 추가**

```python
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pyyaml",
#   "nbformat",
# ]
# ///
```

- [ ] **Step 2: `parse_frontmatter_text()` 헬퍼 추출**

기존 `parse_frontmatter(path)` 로직에서 텍스트 파싱 부분을 분리:

```python
def parse_frontmatter_text(text: str) -> tuple[dict, str]:
    """문자열에서 YAML frontmatter와 본문을 분리."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm = yaml.safe_load(text[3:end]) or {}
    body = text[end + 4:].lstrip("\n")
    return fm, body


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    """content.md에서 YAML frontmatter와 본문을 분리."""
    return parse_frontmatter_text(path.read_text(encoding="utf-8"))
```

- [ ] **Step 3: `parse_notebook()` 함수 추가**

```python
def parse_notebook(path: Path) -> tuple[dict, str]:
    """content.ipynb의 첫 번째 마크다운 셀에서 frontmatter를 파싱하고
    전체 셀 텍스트를 본문으로 반환한다."""
    import nbformat
    nb = nbformat.read(str(path), as_version=4)

    fm: dict = {}
    body_parts: list[str] = []
    first = True

    for cell in nb.cells:
        source = cell.source.strip()
        if not source:
            continue
        if first and cell.cell_type == "markdown" and source.startswith("---"):
            fm, remaining = parse_frontmatter_text(source)
            if remaining.strip():
                body_parts.append(remaining.strip())
            first = False
            continue
        first = False
        if cell.cell_type == "markdown":
            body_parts.append(source)
        elif cell.cell_type == "code":
            body_parts.append(f"```python\n{source}\n```")

    return fm, "\n\n".join(body_parts)
```

- [ ] **Step 4: `scan_posts()` 수정 — ipynb 감지 및 우선순위 적용**

```python
def scan_posts() -> list[dict]:
    """posts/ 디렉토리를 스캔해 frontmatter 기반 포스트 목록 반환.

    content.ipynb가 있으면 content.md보다 우선한다.
    반환 dict의 _body, _path 키는 내부용이며 posts.json에 저장되지 않는다.
    """
    # slug → {"ipynb": Path, "md": Path} 수집
    sources: dict[str, dict] = {}
    for p in sorted(POSTS_DIR.glob("*/content.ipynb")):
        slug = p.parent.name
        if not slug.startswith("_"):
            sources.setdefault(slug, {})["ipynb"] = p
    for p in sorted(POSTS_DIR.glob("*/content.md")):
        slug = p.parent.name
        if not slug.startswith("_"):
            sources.setdefault(slug, {})["md"] = p

    posts = []
    for slug, paths in sorted(sources.items()):
        if "ipynb" in paths:
            fm, body = parse_notebook(paths["ipynb"])
            is_notebook = True
        else:
            fm, body = parse_frontmatter(paths["md"])
            is_notebook = False

        if not fm.get("title"):
            print(f"  [SKIP] {slug}: frontmatter에 title 없음", file=sys.stderr)
            continue

        post: dict = {
            "slug": slug,
            "title": str(fm["title"]),
            "date": str(fm.get("date", date.today())),
            "tags": [str(t) for t in fm.get("tags", [])],
            "summary": str(fm.get("summary") or extract_summary(body)),
            "_body": body,
            "_path": paths.get("ipynb") or paths.get("md"),
        }
        if is_notebook:
            post["notebook"] = True
        posts.append(post)

    return posts
```

- [ ] **Step 5: 커밋**

```bash
git add scripts/posts_list_update.py
git commit -m "feat: ipynb frontmatter 파싱 + scan_posts ipynb 지원"
```

---

## Task 3: 노트북 파서 단위 테스트

**Files:**
- Create: `scripts/test_notebook_parse.py`

- [ ] **Step 1: 테스트 파일 작성**

```python
#!/usr/bin/env python3
"""posts_list_update.py의 ipynb 파싱 로직 단위 테스트."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from posts_list_update import parse_notebook, parse_frontmatter_text, scan_posts


def make_notebook(cells: list[dict]) -> dict:
    """최소한의 nbformat 4 노트북 dict 생성."""
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {"kernelspec": {"name": "python3"}},
        "cells": cells,
    }


def make_md_cell(source: str) -> dict:
    return {"cell_type": "markdown", "source": source, "metadata": {}}


def make_code_cell(source: str) -> dict:
    return {"cell_type": "code", "source": source, "metadata": {}, "outputs": [], "execution_count": None}


def test_parse_frontmatter_text_basic():
    text = "---\ntitle: Hello\ndate: 2026-01-01\n---\n본문"
    fm, body = parse_frontmatter_text(text)
    assert fm["title"] == "Hello"
    assert fm["date"].year == 2026
    assert "본문" in body


def test_parse_frontmatter_text_no_frontmatter():
    text = "그냥 본문"
    fm, body = parse_frontmatter_text(text)
    assert fm == {}
    assert body == "그냥 본문"


def test_parse_notebook_with_frontmatter():
    nb = make_notebook([
        make_md_cell("---\ntitle: 테스트 노트북\ndate: 2026-04-11\ntags: [python]\n---\n소개 문단"),
        make_code_cell("x = 1 + 1\nprint(x)"),
        make_md_cell("## 결론"),
    ])
    with tempfile.NamedTemporaryFile(suffix=".ipynb", mode="w", delete=False, encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False)
        tmp = Path(f.name)
    fm, body = parse_notebook(tmp)
    tmp.unlink()

    assert fm["title"] == "테스트 노트북"
    assert fm["tags"] == ["python"]
    assert "소개 문단" in body
    assert "```python" in body
    assert "x = 1 + 1" in body
    assert "## 결론" in body


def test_parse_notebook_without_frontmatter():
    nb = make_notebook([
        make_md_cell("# 제목 없는 노트북"),
        make_code_cell("print('hello')"),
    ])
    with tempfile.NamedTemporaryFile(suffix=".ipynb", mode="w", delete=False, encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False)
        tmp = Path(f.name)
    fm, body = parse_notebook(tmp)
    tmp.unlink()

    assert fm == {}
    assert "# 제목 없는 노트북" in body


def test_parse_notebook_empty_cells_skipped():
    nb = make_notebook([
        make_md_cell("---\ntitle: 빈 셀 테스트\n---"),
        make_md_cell(""),           # 빈 셀 — 무시
        make_code_cell("a = 1"),
    ])
    with tempfile.NamedTemporaryFile(suffix=".ipynb", mode="w", delete=False, encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False)
        tmp = Path(f.name)
    fm, body = parse_notebook(tmp)
    tmp.unlink()

    assert fm["title"] == "빈 셀 테스트"
    assert "a = 1" in body


if __name__ == "__main__":
    tests = [
        test_parse_frontmatter_text_basic,
        test_parse_frontmatter_text_no_frontmatter,
        test_parse_notebook_with_frontmatter,
        test_parse_notebook_without_frontmatter,
        test_parse_notebook_empty_cells_skipped,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(failed)
```

- [ ] **Step 2: 테스트 실행 (실패 확인)**

```bash
cd /home/ahris/ahrism-pages/scripts && uv run python test_notebook_parse.py
```

Expected: `parse_notebook` / `parse_frontmatter_text` 미정의로 ImportError 또는 실패

- [ ] **Step 3: Task 2 구현 후 테스트 재실행 (통과 확인)**

```bash
cd /home/ahris/ahrism-pages/scripts && uv run python test_notebook_parse.py
```

Expected: `5/5 passed`

- [ ] **Step 4: 커밋**

```bash
git add scripts/test_notebook_parse.py
git commit -m "test: ipynb 파싱 단위 테스트 추가"
```

---

## Task 4: `post.js` — 노트북 정적 렌더링 + JupyterLite 버튼

**Files:**
- Modify: `post.js`

- [ ] **Step 1: `escapeHtml` 헬퍼와 `renderNotebook` 함수를 파일 맨 앞에 추가**

```javascript
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderNotebook(nb) {
  const parts = [];
  let first = true;

  for (const cell of nb.cells) {
    const source = Array.isArray(cell.source) ? cell.source.join('') : (cell.source || '');
    if (!source.trim()) continue;

    // 첫 번째 마크다운 셀이 frontmatter면 건너뜀
    if (first && cell.cell_type === 'markdown' && source.trim().startsWith('---')) {
      first = false;
      continue;
    }
    first = false;

    if (cell.cell_type === 'markdown') {
      parts.push(`<div class="nb-cell nb-markdown">${marked.parse(source)}</div>`);
    } else if (cell.cell_type === 'code') {
      let html = `<div class="nb-cell nb-code"><pre><code class="language-python">${escapeHtml(source)}</code></pre>`;

      const outputs = cell.outputs || [];
      if (outputs.length > 0) {
        html += '<div class="nb-output">';
        for (const out of outputs) {
          if (out.output_type === 'stream') {
            const text = Array.isArray(out.text) ? out.text.join('') : (out.text || '');
            html += `<pre class="nb-stdout">${escapeHtml(text)}</pre>`;
          } else if (out.output_type === 'display_data' || out.output_type === 'execute_result') {
            const data = out.data || {};
            if (data['image/png']) {
              html += `<img src="data:image/png;base64,${data['image/png']}" style="max-width:100%;display:block;margin:0.5rem 0">`;
            } else if (data['image/svg+xml']) {
              const svg = Array.isArray(data['image/svg+xml']) ? data['image/svg+xml'].join('') : data['image/svg+xml'];
              html += `<div class="nb-svg">${svg}</div>`;
            } else if (data['text/html']) {
              const h = Array.isArray(data['text/html']) ? data['text/html'].join('') : data['text/html'];
              html += `<div class="nb-html-out">${h}</div>`;
            } else if (data['text/plain']) {
              const t = Array.isArray(data['text/plain']) ? data['text/plain'].join('') : data['text/plain'];
              html += `<pre class="nb-stdout">${escapeHtml(t)}</pre>`;
            }
          } else if (out.output_type === 'error') {
            html += `<pre class="nb-error">${escapeHtml((out.ename || '') + ': ' + (out.evalue || ''))}</pre>`;
          }
        }
        html += '</div>';
      }

      html += '</div>';
      parts.push(html);
    }
  }
  return parts.join('\n');
}
```

- [ ] **Step 2: 메인 IIFE 내 콘텐츠 렌더링 분기 추가**

기존:
```javascript
  if (mdRes.ok) {
    const md = await mdRes.text();
    document.getElementById('post-content').innerHTML = marked.parse(stripFrontmatter(md));
    document.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));
  } else {
    document.getElementById('post-content').innerHTML = '<p>글을 불러올 수 없습니다.</p>';
  }
```

교체:
```javascript
  if (post && post.notebook) {
    // JupyterLite 실행 버튼 삽입
    const labUrl = `../../lab/index.html?path=posts/${slug}/content.ipynb`;
    document.getElementById('post-header').insertAdjacentHTML('afterend',
      `<div class="nb-open-bar"><a href="${labUrl}" class="nb-open-btn" target="_blank" rel="noopener">▶ JupyterLite에서 실행</a></div>`
    );
    // 노트북 fetch 및 정적 렌더링
    const nbRes = await fetch('./content.ipynb');
    if (nbRes.ok) {
      const nb = await nbRes.json();
      document.getElementById('post-content').innerHTML = renderNotebook(nb);
      document.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));
    } else {
      document.getElementById('post-content').innerHTML = '<p>노트북을 불러올 수 없습니다.</p>';
    }
  } else if (mdRes.ok) {
    const md = await mdRes.text();
    document.getElementById('post-content').innerHTML = marked.parse(stripFrontmatter(md));
    document.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));
  } else {
    document.getElementById('post-content').innerHTML = '<p>글을 불러올 수 없습니다.</p>';
  }
```

- [ ] **Step 3: 커밋**

```bash
git add post.js
git commit -m "feat: post.js에 노트북 정적 렌더링 + JupyterLite 버튼 추가"
```

---

## Task 5: `style.css` — 노트북 셀 스타일

**Files:**
- Modify: `style.css`

- [ ] **Step 1: 노트북 셀 CSS 추가 (파일 끝에 append)**

```css
/* ── Notebook cells ───────────────────────────────────────────── */
.nb-open-bar {
  margin: 1rem 0 1.5rem;
}
.nb-open-btn {
  display: inline-block;
  padding: 0.45rem 1.1rem;
  background: var(--pico-primary-background);
  color: #fff;
  border-radius: 6px;
  font-size: 0.88rem;
  font-weight: 600;
  text-decoration: none;
  transition: opacity 0.15s;
}
.nb-open-btn:hover { opacity: 0.82; }

.nb-cell {
  margin: 0.6rem 0;
}
.nb-code > pre {
  margin-bottom: 0;
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
}
.nb-output {
  background: #0d0d0d;
  border: 1px solid #1e1e1e;
  border-top: none;
  border-radius: 0 0 6px 6px;
  padding: 0.6rem 0.9rem;
  overflow-x: auto;
}
.nb-stdout {
  margin: 0;
  font-size: 0.82rem;
  color: #cccccc;
  white-space: pre-wrap;
  background: transparent;
  border: none;
  padding: 0;
}
.nb-error {
  margin: 0;
  color: #ff5555;
  font-size: 0.82rem;
  white-space: pre-wrap;
  background: transparent;
  border: none;
  padding: 0;
}
.nb-html-out table {
  font-size: 0.82rem;
  border-collapse: collapse;
  width: 100%;
}
.nb-html-out th, .nb-html-out td {
  border: 1px solid #2a2a2a;
  padding: 0.3rem 0.6rem;
  text-align: left;
}
```

- [ ] **Step 2: 커밋**

```bash
git add style.css
git commit -m "style: 노트북 셀 / JupyterLite 버튼 CSS 추가"
```

---

## Task 6: 샘플 노트북 포스트 생성

**Files:**
- Create: `posts/Gaussian_ Z-score_Normalization/content.ipynb`

- [ ] **Step 1: content.ipynb 작성**

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {
  "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
  "language_info": {"name": "python", "version": "3.11.0"}
 },
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": "---\ntitle: \"가우시안 / Z-score 정규화\"\ndate: 2026-04-11\ntags: [통계, 머신러닝, 정규화]\nsummary: \"Z-score 정규화(표준화)의 원리와 구현을 numpy로 직접 실습한다.\"\n---\n\n데이터의 분포를 평균 0, 표준편차 1로 변환하는 **Z-score 정규화(표준화)**를 구현한다."
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": "## 이론\n\n$$z = \\frac{x - \\mu}{\\sigma}$$\n\n- $\\mu$: 평균 (mean)\n- $\\sigma$: 표준편차 (std)\n\nZ-score는 각 값이 평균에서 몇 표준편차 떨어져 있는지를 나타낸다."
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "import numpy as np\n\ndata = np.array([10, 20, 30, 40, 50], dtype=float)\nmu = data.mean()\nsigma = data.std()\n\nprint(f'평균: {mu}, 표준편차: {sigma}')"
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "def z_score(x: np.ndarray) -> np.ndarray:\n    return (x - x.mean()) / x.std()\n\nnormalized = z_score(data)\nprint('원본:', data)\nprint('정규화:', normalized)\nprint('평균 확인:', normalized.mean().round(10))\nprint('표준편차 확인:', normalized.std().round(10))"
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": "## 시각화\n\n`matplotlib`으로 원본과 정규화된 분포를 비교한다."
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": "import matplotlib.pyplot as plt\n\nfig, axes = plt.subplots(1, 2, figsize=(8, 3))\naxes[0].hist(data, bins=5, color='#4a62ff')\naxes[0].set_title('원본 데이터')\naxes[1].hist(normalized, bins=5, color='#dc00c9')\naxes[1].set_title('Z-score 정규화')\nplt.tight_layout()\nplt.show()"
  }
 ]
}
```

- [ ] **Step 2: 빌드 실행 (--posts-only, ML 모델 로딩 없이)**

```bash
cd /home/ahris/ahrism-pages/scripts && uv run python post_update.py --posts-only
```

Expected: `Gaussian_ Z-score_Normalization` 포스트가 posts.json에 포함되고 `"notebook": true` 필드 확인

- [ ] **Step 3: posts.json에서 notebook 필드 확인**

```bash
grep -A5 "Gaussian" /home/ahris/ahrism-pages/blog/posts.json
```

Expected 출력:
```json
{
  "slug": "Gaussian_ Z-score_Normalization",
  "title": "가우시안 / Z-score 정규화",
  "notebook": true,
  ...
}
```

- [ ] **Step 4: 전체 빌드 (임베딩 + 그래프)**

```bash
cd /home/ahris/ahrism-pages/scripts && uv run python post_update.py
```

Expected: 정상 완료, graph.json에 `Gaussian_ Z-score_Normalization` 노드 포함

- [ ] **Step 5: 로컬 서버로 확인**

```bash
cd /home/ahris/ahrism-pages && python3 -m http.server 8080
```

브라우저에서 `http://localhost:8080/posts/Gaussian_ Z-score_Normalization/` 접속.  
- 셀 정적 렌더링 확인  
- "▶ JupyterLite에서 실행" 버튼 확인 (로컬에서는 /lab/ 없어서 링크만 보임)

- [ ] **Step 6: 커밋**

```bash
git add posts/Gaussian_\ Z-score_Normalization/content.ipynb blog/posts.json blog/graph.json blog/tags.json
git commit -m "post: Gaussian Z-score 정규화 노트북 포스트 추가"
```

---

## Task 7: Push + GitHub Pages 확인

- [ ] **Step 1: ⚠️ 수동 확인 — GitHub Pages 소스 설정**

GitHub 리포 → Settings → Pages → Source: **GitHub Actions** 로 설정됨을 확인

- [ ] **Step 2: Push**

```bash
git push origin main
```

- [ ] **Step 3: Actions 빌드 확인**

GitHub → Actions 탭에서 "Deploy to GitHub Pages" 워크플로우 성공 확인

- [ ] **Step 4: 배포된 사이트에서 JupyterLite 동작 확인**

`https://<username>.github.io/.../posts/Gaussian_ Z-score_Normalization/` 접속  
- 노트북 셀 정적 렌더링  
- "▶ JupyterLite에서 실행" 클릭 → `/lab/index.html?path=posts/...` 에서 노트북 실행 가능 확인

---

## Verification Summary

| 검증 항목 | 방법 |
|----------|------|
| 파서 단위 테스트 | `uv run python test_notebook_parse.py` → `5/5 passed` |
| posts.json 생성 | `"notebook": true` 필드 포함 여부 확인 |
| 전체 빌드 | `uv run python post_update.py` 정상 완료 |
| 로컬 렌더링 | `localhost:8080`에서 셀 미리보기 + 버튼 표시 |
| JupyterLite 실행 | 배포 후 `/lab/`에서 노트북 열기 + 코드 셀 실행 |
