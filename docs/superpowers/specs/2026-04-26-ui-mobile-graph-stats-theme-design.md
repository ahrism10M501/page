# UI Mobile, Graph, Stats, and Theme Design

Date: 2026-04-26

## Goal

Improve the visible site experience before deeper Python and JavaScript refactors. This phase focuses on mobile navigation, Twinkle tag access, the home graph interaction, home blog activity statistics, and reducing overuse of the current pink accent.

## Scope

In scope:

- Replace the cramped mobile sidebar experience with a slim mobile header and drawer.
- Improve mobile Twinkle tag browsing with a readable page-level filter area.
- Remove the home graph pull-to-expand gesture that conflicts with Chrome pull-to-refresh.
- Add a fullscreen graph exploration mode opened by an explicit control.
- Add static blog activity statistics derived from existing local JSON files.
- Introduce semantic theme tokens and reduce pink to rare emphasis states.

Out of scope:

- Visitor counts or analytics integrations.
- Server-side APIs or persistent runtime state.
- Python pipeline behavior changes.
- Large visual redesign of every page.

## Current Problems

Mobile navigation currently depends on a fixed sidebar pattern that feels cramped on phones. Twinkle tags are available as small inline chips on mobile, but the control is not prominent or comfortable enough for repeated filtering.

The home graph uses document-level touch events to implement pull-to-expand. On mobile Chrome this conflicts with browser pull-to-refresh, and the graph changes height while the user is dragging, which makes the interaction feel unstable.

The home page does not summarize blog activity. It shows content and graph exploration, but not the user's posting rhythm, tag spread, or graph connectivity.

The theme uses `#dc00c9` for many unrelated meanings: primary color, active navigation, dates, graph hover/root styles, selected filters, progress cursor, and Twinkle active states. This makes the visual language feel saturated and less intentional.

## Design

### 1. Mobile Header And Drawer

On screens up to the mobile breakpoint, replace the current sidebar-first presentation with a slim fixed or sticky top header. The header contains a menu button, site identity, and the current section affordance. Tapping the menu opens a drawer with the same navigation items currently sourced from `templates/nav.json`.

The desktop sidebar remains the primary desktop navigation. The change should preserve existing navigation URLs and active-page behavior.

Expected behavior:

- Header is visible on mobile pages.
- Drawer opens and closes with the menu button.
- Tapping outside the drawer closes it.
- Navigation items continue to use `templates/nav.json`.
- Body content has enough top spacing to avoid being covered by the header.

### 2. Twinkle Mobile Tags

For Twinkle on mobile, keep tags inside the page rather than hiding them behind the global drawer. The filter area should be larger and easier to scan than the current compact chip row.

Expected behavior:

- Archive sidebar remains desktop-only.
- Mobile tag filters are shown near the top of the Twinkle feed.
- Active tag state is clear without relying on pink.
- Filtering, pagination reset, hash clearing, and archive state remain consistent with current behavior.

### 3. Home Graph Fullscreen Mode

Remove the pull-to-expand gesture from `src/home-graph.js`. The home graph becomes a stable preview. A visible control opens a fullscreen graph mode.

Fullscreen mode should:

- Cover the viewport with the graph.
- Lock or avoid background page scrolling while open.
- Provide a clear close control.
- Preserve zoom preset controls.
- Avoid document-level pull-down gestures.
- Trigger Cytoscape resize/fit after entering and leaving fullscreen mode so the graph is correctly framed.

The existing fallback list behavior remains if graph data is unavailable.

### 4. Home Blog Activity Statistics

Add a home statistics section using existing static data. Do not implement visitor counts in this phase.

Data sources:

- `blog/posts.json` for post count, dates, tags, notebook count, and recent activity.
- `blog/graph.json` for node and edge counts.
- `twinkle/twinkles.json` for Twinkle count.

Stats to display:

- Total posts.
- Posts in the last 90 days.
- Most-used tags.
- Notebook count.
- Graph connections count.
- Posting activity heatmap grouped by date, similar in spirit to GitHub contribution activity.
- Twinkle count.

The statistics will be computed in frontend JavaScript from static JSON. No generated stats file is part of this phase.

### 5. Theme Token Cleanup

Introduce semantic CSS custom properties near the top of `style.css`. Existing Pico variables may remain, but site-specific usage should move toward semantic tokens.

Token roles:

- `--color-bg`
- `--color-surface`
- `--color-border`
- `--color-text`
- `--color-muted`
- `--color-accent`
- `--color-accent-strong`
- `--color-info`
- `--color-danger`
- `--color-success`

Pink should be reserved for rare emphasis or brand moments. Active navigation, selected filters, graph hover, dates, and metadata should use more neutral or blue/cyan-oriented tokens unless a specific element needs the brand accent.

## Implementation Boundaries

Primary files involved:

- `templates/base.html`
- `templates/partials/sidebar.html`
- `templates/pages/home.html`
- `templates/pages/twinkle.html`
- `src/sidebar.js`
- `src/home-graph.js`
- `src/twinkle-feed.js`
- `src/home-stats.js`
- `style.css`

Do not change the Python pipeline during this UI phase.

## Testing And Verification

Automated checks:

- `uv run pytest`
- `uv run python scripts/build_site.py`

Manual/browser checks:

- Mobile width around 375px and 430px.
- Desktop width around 1280px.
- Home page graph preview opens fullscreen and closes correctly.
- Mobile Chrome-like behavior no longer depends on pull-down to expand the graph.
- Twinkle mobile filters are readable and still filter correctly.
- Desktop Twinkle archive still works.
- Generated pages do not shift footer or content under fixed UI.

## Acceptance Criteria

- Mobile navigation is easier to access and does not feel like a compressed desktop sidebar.
- Twinkle tags are readable and usable on phones.
- Home graph no longer triggers or competes with pull-to-refresh behavior.
- Fullscreen graph mode is explicit, reversible, and stable.
- Home page includes local blog activity statistics, excluding visitor counts.
- Pink is no longer the dominant state color across unrelated UI elements.
- Existing tests and static build pass.
