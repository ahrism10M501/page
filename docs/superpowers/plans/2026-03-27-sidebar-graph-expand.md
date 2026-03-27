# Sidebar Nav + Graph Upward Expand — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fixed VSCode-style icon sidebar to all pages replacing the top nav, and make the index graph expand upward to fill the full viewport on scroll.

**Architecture:** Shared `sidebar.js` (40줄) handles panel toggle/navigation. All sidebar visuals live in `style.css`. HTML change is mechanical across 13 files (remove `<header>`, insert `<aside>`). Graph upward expand is a `#post-graph` padding-top collapse + `EXPANDED_VH 100` change, index.html only.

**Tech Stack:** Vanilla HTML/CSS/JS, Pico.css v2 (existing)

---

## File Map

| File | 변경 |
|------|------|
| `style.css` | 사이드바/패널 CSS + `#post-graph` 패딩 트랜지션 추가 |
| `sidebar.js` | 신규 — 패널 토글, 이동, 패널 외부 클릭 닫기 |
| `index.html` | `<header>` 제거, `<aside>` 삽입, graph expand JS 수정 |
| `blog/index.html` | `<header>` 제거, `<aside>` 삽입 |
| `posts/_template/index.html` | `<header>` 제거, `<aside>` 삽입 |
| `posts/python-performance/index.html` | 동일 |
| `posts/docker-container/index.html` | 동일 |
| `posts/hello-world/index.html` | 동일 |
| `posts/test-post-1/index.html` | 동일 |
| `posts/opencv-basics/index.html` | 동일 |
| `posts/간단ALU만들기_프로젝트/index.html` | 동일 |
| `posts/인공신경망1/index.html` | 동일 |
| `posts/딥러닝과_신경망/index.html` | 동일 |

---

### Task 1: Sidebar CSS (`style.css`)

**Files:**
- Modify: `style.css`

- [ ] **Step 1: `body` 규칙에 `padding-left` 추가**

`style.css`에서 기존:
```css
body { overscroll-behavior-y: contain; }
```
를 다음으로 교체:
```css
body {
  overscroll-behavior-y: contain;
  padding-left: 48px;
}
```

- [ ] **Step 2: 사이드바 + 패널 CSS를 `style.css` 끝에 추가**

```css
/* ── Sidebar ─────────────────────────────────────────── */
#sidebar {
  position: fixed;
  left: 0; top: 0;
  width: 48px; height: 100vh;
  background: #111111;
  border-right: 1px solid #1e1e1e;
  z-index: 100;
  display: flex;
  flex-direction: column;
}
.sidebar-icons {
  display: flex;
  flex-direction: column;
}
.sidebar-btn {
  width: 48px; height: 48px;
  background: transparent;
  border: none;
  border-left: 2px solid transparent;
  color: #555;
  font-size: 1.2rem;
  cursor: pointer;
  position: relative;
  transition: color 0.15s, border-color 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.sidebar-btn:hover { color: #cccccc; }
.sidebar-btn.active {
  color: #dc00c9;
  border-left-color: #dc00c9;
}
/* hover tooltip */
.sidebar-btn::after {
  content: attr(data-label);
  position: absolute;
  left: calc(100% + 8px); top: 50%;
  transform: translateY(-50%);
  background: #1e1e1e;
  color: #ccc;
  font-size: 0.7rem;
  white-space: nowrap;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.15s;
  z-index: 200;
}
.sidebar-btn:hover::after { opacity: 1; }

/* Sidebar panel (overlay) */
.sidebar-panel {
  position: fixed;
  left: 48px; top: 0;
  width: 220px; height: 100vh;
  background: #111111;
  border-right: 1px solid #1e1e1e;
  z-index: 99;
  transform: translateX(-100%);
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  overflow-y: auto;
}
.sidebar-panel.open { transform: translateX(0); }
.panel-header {
  padding: 1rem 1rem 0.5rem;
  font-size: 0.7rem;
  color: #dc00c9;
  text-transform: uppercase;
  letter-spacing: 2px;
  border-bottom: 1px solid #1e1e1e;
  margin-bottom: 0.5rem;
}
.panel-placeholder {
  padding: 0.5rem 1rem;
  color: #555;
  font-size: 0.85rem;
}

/* ── Index graph upward expand ───────────────────────── */
#post-graph {
  padding-top: 1.5rem;
  transition: padding-top 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}
#post-graph.expanded { padding-top: 0; }
#graph-hint { transition: opacity 0.2s ease; }
#post-graph.expanded #graph-hint {
  opacity: 0;
  pointer-events: none;
}
```

- [ ] **Step 3: 커밋**

```bash
git add style.css
git commit -m "style: sidebar + graph upward expand CSS"
```

---

### Task 2: `sidebar.js` 생성

**Files:**
- Create: `sidebar.js`

- [ ] **Step 1: `sidebar.js` 작성**

```javascript
// sidebar.js — shared sidebar: panel toggle, navigation, outside-click close
(function () {
  // 패널 토글 버튼 (data-panel 속성 있음)
  document.querySelectorAll('.sidebar-btn[data-panel]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var panelId = 'panel-' + btn.dataset.panel;
      var panel = document.getElementById(panelId);
      if (!panel) return;
      var isOpen = panel.classList.contains('open');
      document.querySelectorAll('.sidebar-panel').forEach(function (p) {
        p.classList.remove('open');
      });
      if (!isOpen) panel.classList.add('open');
    });
  });

  // 이동 버튼 (data-href 속성 있음)
  document.querySelectorAll('.sidebar-btn[data-href]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      window.location.href = btn.dataset.href;
    });
  });

  // 사이드바 외부 클릭 시 패널 닫기
  document.addEventListener('click', function (e) {
    if (!e.target.closest('#sidebar')) {
      document.querySelectorAll('.sidebar-panel').forEach(function (p) {
        p.classList.remove('open');
      });
    }
  });
})();
```

- [ ] **Step 2: 커밋**

```bash
git add sidebar.js
git commit -m "feat: sidebar.js — panel toggle, nav, outside-click close"
```

---

### Task 3: `index.html`

**Files:**
- Modify: `index.html`

- [ ] **Step 1: `<header>` 제거**

다음 블록 전체 삭제:
```html
  <header class="container">
    <nav>
      <ul><li><strong><a href="./">ahrism</a></strong></li></ul>
      <ul>
        <li><a href="#about" class="active">About</a></li>
        <li><a href="./blog/">Blog</a></li>
      </ul>
    </nav>
  </header>
```

- [ ] **Step 2: `<aside>` 삽입 — `<body>` 바로 다음**

```html
  <aside id="sidebar">
    <div class="sidebar-icons">
      <button class="sidebar-btn active" data-label="Home" data-href="./">⌂</button>
      <button class="sidebar-btn" data-panel="about" data-label="About">◉</button>
      <button class="sidebar-btn" data-label="Blog" data-href="./blog/">≡</button>
      <button class="sidebar-btn" data-panel="github" data-label="GitHub">⬡</button>
    </div>
    <div id="panel-about" class="sidebar-panel">
      <div class="panel-header">About</div>
      <p class="panel-placeholder">준비 중</p>
    </div>
    <div id="panel-github" class="sidebar-panel">
      <div class="panel-header">GitHub</div>
      <p class="panel-placeholder">준비 중</p>
    </div>
  </aside>
```

- [ ] **Step 3: graph expand JS 수정 — `EXPANDED_VH` + `.expanded` 클래스 토글**

인라인 `<script>` (rubber band scroll 블록) 내에서:

`EXPANDED_VH = 80` → `EXPANDED_VH = 100`

`snapExpand` 함수:
```javascript
  function snapExpand() {
    expanded = true;
    snapTo(EXPANDED_VH);
    document.getElementById('post-graph').classList.add('expanded');
  }
```

`snapCollapse` 함수:
```javascript
  function snapCollapse() {
    expanded = false;
    snapTo(DEFAULT_VH);
    document.getElementById('post-graph').classList.remove('expanded');
  }
```

- [ ] **Step 4: `</body>` 직전에 `sidebar.js` script 태그 추가**

```html
  <script src="./sidebar.js"></script>
```

- [ ] **Step 5: 시각 검증**

`python3 -m http.server 8080` 실행 후 `http://localhost:8080/` 확인:
- 좌측 48px 다크 사이드바 표시
- ⌂ 버튼 magenta 활성 (border-left + 색상)
- 버튼 hover → 오른쪽에 레이블 tooltip 표시
- ◉ 클릭 → "About / 준비 중" 패널 슬라이드인
- ⬡ 클릭 → "GitHub / 준비 중" 패널 슬라이드인
- 패널 외부 클릭 → 패널 닫힘
- 스크롤 위 → 그래프 `100vh`로 확장, 상단 패딩 사라지며 위로도 차오름, hint 페이드아웃
- 스크롤 아래 → 원래 크기로 복원

- [ ] **Step 6: 커밋**

```bash
git add index.html
git commit -m "feat: index — remove header, add sidebar, graph full-height expand"
```

---

### Task 4: `blog/index.html`

**Files:**
- Modify: `blog/index.html`

- [ ] **Step 1: `<header>` 제거**

다음 블록 전체 삭제:
```html
  <header class="container">
    <nav>
      <ul><li><strong><a href="../">ahrism</a></strong></li></ul>
      <ul>
        <li><a href="../#about">About</a></li>
        <li><a href="./" class="active">Blog</a></li>
      </ul>
    </nav>
  </header>
```

- [ ] **Step 2: `<aside>` 삽입 — `<body>` 바로 다음**

```html
  <aside id="sidebar">
    <div class="sidebar-icons">
      <button class="sidebar-btn" data-label="Home" data-href="../">⌂</button>
      <button class="sidebar-btn" data-panel="about" data-label="About">◉</button>
      <button class="sidebar-btn active" data-label="Blog" data-href="./">≡</button>
      <button class="sidebar-btn" data-panel="github" data-label="GitHub">⬡</button>
    </div>
    <div id="panel-about" class="sidebar-panel">
      <div class="panel-header">About</div>
      <p class="panel-placeholder">준비 중</p>
    </div>
    <div id="panel-github" class="sidebar-panel">
      <div class="panel-header">GitHub</div>
      <p class="panel-placeholder">준비 중</p>
    </div>
  </aside>
```

- [ ] **Step 3: `</body>` 직전에 `sidebar.js` script 태그 추가**

```html
  <script src="../sidebar.js"></script>
```

- [ ] **Step 4: 시각 검증**

`http://localhost:8080/blog/` 확인:
- 사이드바 표시, ≡ Blog 버튼 magenta 활성
- 기존 검색/태그/리스트 기능 정상 동작

- [ ] **Step 5: 커밋**

```bash
git add blog/index.html
git commit -m "feat: blog — remove header, add sidebar"
```

---

### Task 5: `posts/_template/index.html`

**Files:**
- Modify: `posts/_template/index.html`

- [ ] **Step 1: `<header>` 제거**

다음 블록 전체 삭제:
```html
  <header class="container">
    <nav>
      <ul><li><strong><a href="../../">ahrism</a></strong></li></ul>
      <ul>
        <li><a href="../../#about">About</a></li>
        <li><a href="../../blog/" class="active">Blog</a></li>
      </ul>
    </nav>
  </header>
```

- [ ] **Step 2: `<aside>` 삽입 — `<body>` 바로 다음**

```html
  <aside id="sidebar">
    <div class="sidebar-icons">
      <button class="sidebar-btn" data-label="Home" data-href="../../">⌂</button>
      <button class="sidebar-btn" data-panel="about" data-label="About">◉</button>
      <button class="sidebar-btn active" data-label="Blog" data-href="../../blog/">≡</button>
      <button class="sidebar-btn" data-panel="github" data-label="GitHub">⬡</button>
    </div>
    <div id="panel-about" class="sidebar-panel">
      <div class="panel-header">About</div>
      <p class="panel-placeholder">준비 중</p>
    </div>
    <div id="panel-github" class="sidebar-panel">
      <div class="panel-header">GitHub</div>
      <p class="panel-placeholder">준비 중</p>
    </div>
  </aside>
```

- [ ] **Step 3: `</body>` 직전에 `sidebar.js` script 태그 추가**

```html
  <script src="../../sidebar.js"></script>
```

- [ ] **Step 4: 커밋**

```bash
git add posts/_template/index.html
git commit -m "feat: post template — remove header, add sidebar"
```

---

### Task 6: 기존 포스트 9개 일괄 업데이트

**Files:**
- `posts/python-performance/index.html`
- `posts/docker-container/index.html`
- `posts/hello-world/index.html`
- `posts/test-post-1/index.html`
- `posts/opencv-basics/index.html`
- `posts/간단ALU만들기_프로젝트/index.html`
- `posts/인공신경망1/index.html`
- `posts/딥러닝과_신경망/index.html`

모두 Task 5와 동일한 변경 (경로 깊이 `../../` 동일).

- [ ] **Step 1: 각 파일에 동일하게 적용**

각 파일마다:
1. `<header class="container">...</header>` 블록 제거 (Task 5 Step 1과 동일한 코드)
2. `<body>` 바로 다음에 `<aside>` 삽입 (Task 5 Step 2와 동일한 코드)
3. `</body>` 직전에 `<script src="../../sidebar.js"></script>` 추가

`← Blog` 링크(`<a href="../../blog/" ...>← Blog</a>`)는 `<main>` 내부에 있으므로 **그대로 유지**.

- [ ] **Step 2: 시각 검증**

`http://localhost:8080/posts/hello-world/` 확인:
- 사이드바 표시, Blog 버튼 활성
- `← Blog` 링크 정상 표시
- 포스트 콘텐츠 정상 렌더링
- 하단 Related Posts 서브그래프 정상 동작

- [ ] **Step 3: 커밋**

```bash
git add \
  posts/python-performance/index.html \
  posts/docker-container/index.html \
  posts/hello-world/index.html \
  posts/test-post-1/index.html \
  posts/opencv-basics/index.html \
  "posts/간단ALU만들기_프로젝트/index.html" \
  posts/인공신경망1/index.html \
  posts/딥러닝과_신경망/index.html
git commit -m "feat: all posts — remove header, add sidebar"
```
