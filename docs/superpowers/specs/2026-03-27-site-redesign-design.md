# Site Redesign — Design Spec

**Date:** 2026-03-27
**Goal:** 가볍고 빠른 포트폴리오+블로그 리디자인. 데스크탑/모바일 동시 지원. 동접 200명 기준 (정적 파일, CDN).

---

## 1. 전체 방향

**에디토리얼/매거진 톤** — 좌측 보더 강조, 섹션 레이블(소문자 uppercase letter-spacing), 화살표 링크(`→`), 날짜 우측 정렬. Pico.css 의존성 유지, `style.css` 개선.

**구현 방식 B** — CSS 전면 개선 + index.html에만 커스텀 spring scroll JS (~80줄). 나머지 페이지는 CSS만.

**성능 제약** — CSS 추가 ~100줄 이내. JS 추가 ~80줄(index.html 한정). 새 CDN 의존성 없음. 애니메이션은 `transform/opacity`만 (GPU 가속).

---

## 2. index.html — 그래프 헤더 + 스프링 확장

### 레이아웃 상태

| 상태 | 그래프 높이 | 트리거 |
|------|------------|--------|
| 기본 | `--graph-h: 45vh` | 페이지 로드 |
| 당기는 중 | `45vh + delta * 0.4` (rubber band 감쇠) | 최상단에서 위로 드래그 |
| 확장 "톡!" | `--graph-h: 80vh` | delta > 80px |
| 복귀 | `45vh` (spring ease) | 아래 스크롤 |

### 구현 세부

- **CSS variable 제어:** `--graph-h` 변수를 JS에서 직접 수정 → `height: var(--graph-h)` 적용. `transition: height 0.35s cubic-bezier(0.34, 1.56, 0.64, 1)` (spring easing).
- **드래그 중 transition 처리:** `touchstart`/`wheel` 시작 시 `transition: none` 설정 → 연속 드래그를 lag 없이 따라감. `touchend` 또는 snap 트리거 시 transition 복원 후 최종 높이 설정.
- **이벤트:**
  - 터치: `touchstart` / `touchmove` / `touchend` on `document`
  - 휠: `wheel` event, `scrollTop === 0 && deltaY < 0` 조건
- **모바일 pull-to-refresh 방지:** `body { overscroll-behavior-y: contain; }` — 상시 적용 (iOS Safari 대응)
- **힌트 텍스트:** 그래프 상단에 `↑ PULL` 문구, `color: #2a2a2a` (아주 연하게)

### About 섹션 에디토리얼화

```
[좌측 2px magenta 보더]
  ABOUT                    ← 0.7rem, letter-spacing: 2px, #dc00c9
  ahrism                   ← h1, 기존 유지
  Building Practical...    ← p, 기존 유지
[태그 칩들]
[관심사 본문]
[PROJECTS 레이블 + 카드]
[학력]
Blog →                     ← #4a62ff, 섹션 하단
```

---

## 3. blog/index.html

### 변경 사항

- **제목 제거:** `<h1>Blog</h1>` 삭제
- **검색바 최상단:** nav 바로 아래 첫 번째 요소로 이동
- **뷰 토글:** 텍스트 버튼 → 아이콘만 (`⬡` / `☰`), 우측 정렬, 태그 필터 행 끝에 위치
- **포스트 아이템 에디토리얼화:**
  - 날짜 우측 정렬 (`Jan 15` 형식)
  - 요약 기본 표시 (현재도 있음, 스타일만 개선)
- **태그 필터:** "전체" 칩 추가 (첫 번째, 클릭 시 전체 해제)
- **키워드 가중 토글:** 검색어 입력 시에만 노출 (기본 숨김)

---

## 4. 포스트 페이지 (posts/_template/index.html)

### 변경 사항

- **포스트 헤더 에디토리얼화:**
  ```
  [좌측 2px magenta 보더]
    2024-01-15             ← 날짜, 0.7rem label 스타일
    포스트 제목             ← h1
    [태그 칩들]
  [수평선 divider]
  [본문]
  ```
- **뒤로가기 링크:** `← Back to Blog` → `← Blog`, `color: #444`
- **관련 글 섹션 레이블:** `관련 글 탐색` → `Related Posts`, `color: #555`

---

## 5. style.css — 에디토리얼 컴포넌트 추가

기존 변수/컴포넌트 유지. 추가/변경:

```css
/* Editorial left-border block */
.editorial-header {
  border-left: 2px solid var(--pico-primary);
  padding-left: 0.75rem;
}
.editorial-label {
  font-size: 0.7rem;
  color: var(--pico-primary);
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-bottom: 0.2rem;
}

/* Arrow link */
.link-arrow { color: var(--pico-secondary); }
.link-arrow::after { content: ' →'; }

/* Post list item (에디토리얼) */
.post-item {
  display: flex;          /* 기존 block → flex */
  flex-direction: column;
}
.post-item-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}
.post-date-inline {
  font-size: 0.75rem;
  color: #444;
  white-space: nowrap;
}

/* Graph container height var */
.graph-container {
  height: var(--graph-h, 45vh);
  transition: height 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

---

## 6. 성능 / 반응형

- **모바일:** 그래프 기본 높이 `--graph-h: 40vh` (미디어쿼리 `max-width: 640px`)
- **애니메이션:** `transform`, `opacity`, `height` (var 경유)만 사용. `will-change: height` 그래프 컨테이너에만
- **정적 파일:** GitHub Pages CDN. 동접 200명 = 문제없음
- **pull-to-refresh 충돌:** `overscroll-behavior-y: contain` body에 상시 적용 (iOS Safari 지원)

---

## 7. 파일 변경 범위

| 파일 | 변경 |
|------|------|
| `style.css` | 에디토리얼 컴포넌트 추가, graph-h var, post-item 수정 |
| `index.html` | About 섹션 마크업 + 인라인 spring scroll JS |
| `blog/index.html` | 검색바 이동, 제목 제거, 뷰토글 아이콘화 |
| `app.js` | `renderPostList` 에디토리얼 마크업으로 수정 |
| `posts/_template/index.html` | 포스트 헤더 마크업 수정 |

> `graph.js`, `post.js`, `scripts/` — 변경 없음
