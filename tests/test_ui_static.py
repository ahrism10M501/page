from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def css_rule(css: str, selector: str) -> str:
    match = re.search(rf"{re.escape(selector)}\s*\{{(?P<body>.*?)\n\}}", css, re.DOTALL)
    assert match is not None, f"{selector} rule not found"
    return match.group("body")


def test_style_defines_semantic_theme_tokens():
    css = read("style.css")
    for token in [
        "--color-bg",
        "--color-surface",
        "--color-surface-raised",
        "--color-border",
        "--color-text",
        "--color-muted",
        "--color-accent",
        "--color-accent-strong",
        "--color-info",
        "--color-danger",
        "--color-success",
    ]:
        assert token in css


def test_pink_is_not_used_as_general_state_color():
    css = read("style.css")
    assert css.count("#dc00c9") <= 4


def test_stale_info_color_channels_not_in_css():
    css = read("style.css")
    assert "74, 98, 255" not in css, "stale #4a62ff rgba channels found — use color-mix(var(--color-info)) instead"


def test_semantic_color_tokens_use_valid_hex_values():
    css = read("style.css")
    root_match = re.search(r":root\s*\{(?P<body>.*?)\n\}", css, re.DOTALL)
    assert root_match is not None

    declarations = re.findall(
        r"(--color-[\w-]+)\s*:\s*(#[0-9a-fA-F]+)\s*;",
        root_match.group("body"),
    )
    assert declarations

    for token, value in declarations:
        assert re.fullmatch(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?", value), (
            f"{token} uses invalid hex color {value}"
        )
        assert value.lower() != "#6d4ef0", f"{token} uses rejected hover typo {value}"


def test_sidebar_partial_contains_mobile_header_and_drawer():
    html = read("templates/partials/sidebar.html")
    assert 'id="mobile-site-header"' in html
    assert 'id="mobile-nav-toggle"' in html
    assert 'id="mobile-nav-drawer"' in html
    assert 'mobile-nav-link' in html
    assert 'aria-expanded="false"' in html
    assert 'aria-hidden="true"' in html
    assert "inert" in html


def test_sidebar_js_controls_mobile_drawer():
    js = read("src/sidebar.js")
    assert "mobile-nav-toggle" in js
    assert "mobile-nav-drawer" in js
    assert "mobile-nav-open" in js
    assert "setAttribute('aria-expanded'" in js
    assert "setAttribute('aria-hidden'" in js
    assert ".inert" in js
    assert "tabIndex" in js
    assert "querySelectorAll('.mobile-nav-link')" in js


def test_mobile_drawer_has_keyboard_focus_styles():
    css = read("style.css")
    assert "#mobile-nav-toggle:focus-visible" in css
    assert ".mobile-nav-link:focus-visible" in css


def test_twinkle_template_has_mobile_filter_region():
    html = read("templates/pages/twinkle.html")
    assert 'class="twinkle-mobile-filter-panel"' in html
    assert 'id="mobile-tags"' in html
    assert '모바일 트윙클 필터' in html


def test_twinkle_tags_render_as_buttons_with_pressed_state():
    js = read("src/twinkle-feed.js")
    assert '<button type="button"' in js
    assert "aria-pressed" in js
    assert "chip.dataset.tag" in js


def test_twinkle_tag_data_attribute_uses_attribute_safe_escape():
    js = read("src/twinkle-feed.js")
    assert "function escapeAttr" in js
    assert ".replace(/&/g, '&amp;')" in js
    assert ".replace(/\"/g, '&quot;')" in js
    assert ".replace(/'/g, '&#39;')" in js
    assert 'data-tag="${escapeAttr(tag)}"' in js


def test_twinkle_tag_buttons_have_focus_visible_styles():
    css = read("style.css")
    assert ".archive-tag-chip:focus-visible" in css
    assert ".twinkle-mobile-tag-chip:focus-visible" in css


def test_archive_tag_button_has_reset_styles():
    css = read("style.css")
    archive_rule = css_rule(css, ".archive-tag-chip")
    assert "appearance: none;" in archive_rule
    assert "background:" in archive_rule
    assert "font-family: inherit;" in archive_rule
    assert "box-sizing: border-box;" in archive_rule


def test_home_template_uses_explicit_graph_controls():
    html = read("templates/pages/home.html")
    assert 'id="graph-open-btn"' in html
    assert 'aria-controls="graph-stage"' in html
    assert 'aria-expanded="false"' in html
    assert 'id="graph-stage"' in html
    assert 'id="graph-close-btn"' in html
    assert 'aria-controls="graph-stage"' in html
    assert "Explore graph" in html


def test_home_graph_removes_pull_gesture_and_uses_fullscreen_mode():
    js = read("src/home-graph.js")
    assert "startPullToExpand" not in js
    assert "touchstart" not in js
    assert "touchmove" not in js
    assert "graph-fullscreen" in js
    assert "graph-modal-open" in js
    assert ".resize()" in js


def test_home_graph_fallback_disables_dead_open_affordance():
    js = read("src/home-graph.js")
    assert "disableGraphControlsForFallback" in js
    assert "openBtn.disabled = true" in js
    assert "toolbar.hidden = true" in js


def test_home_graph_resets_zoom_preset_state_after_fit():
    js = read("src/home-graph.js")
    assert "function resetZoomPresetState()" in js
    assert "btn.dataset.zoom === '1'" in js
    assert "zoomBaseZoom = cy.zoom()" in js
    refresh_rule = re.search(r"function refreshGraphFrame\(cy\)\s*\{(?P<body>.*?)\n  \}", js, re.DOTALL)
    assert refresh_rule is not None
    assert "resetZoomPresetState();" in refresh_rule.group("body")


def test_home_graph_fullscreen_accessibility_and_focus_contracts():
    js = read("src/home-graph.js")
    for expected in [
        "openBtn.setAttribute('aria-expanded', 'true')",
        "openBtn.setAttribute('aria-expanded', 'false')",
        "stage.setAttribute('role', 'dialog')",
        "stage.setAttribute('aria-modal', 'true')",
        "stage.removeAttribute('role')",
        "stage.removeAttribute('aria-modal')",
        "closeBtn.focus()",
        "openBtn.focus()",
    ]:
        assert expected in js


def test_home_graph_zoom_controls_only_focusable_in_fullscreen():
    html = read("templates/pages/home.html")
    js = read("src/home-graph.js")
    css = read("style.css")
    assert 'tabindex="-1"' in html
    assert "function setZoomPresetsFocusable(isFocusable)" in js
    assert "btn.tabIndex = isFocusable ? 0 : -1" in js
    assert "setZoomPresetsFocusable(true)" in js
    assert "setZoomPresetsFocusable(false)" in js
    assert ".zoom-preset:focus-visible" in css
    assert "#graph-open-btn:focus-visible" in css
    assert "#graph-close-btn:focus-visible" in css


def test_home_graph_fullscreen_traps_tab_focus():
    js = read("src/home-graph.js")
    focusables_rule = re.search(r"function getFullscreenFocusables\(\)\s*\{(?P<body>.*?)\n    \}", js, re.DOTALL)
    assert focusables_rule is not None
    assert "return [closeBtn]" in focusables_rule.group("body")
    assert "offsetParent" not in focusables_rule.group("body")
    for expected in [
        "function handleFullscreenKeydown(e)",
        "e.key === 'Tab'",
        "document.activeElement",
        "getFullscreenFocusables()",
        "focusables[0].focus()",
        "focusables[focusables.length - 1].focus()",
        "e.preventDefault()",
    ]:
        assert expected in js


def test_home_template_includes_stats_mount_and_script():
    html = read("templates/pages/home.html")
    assert 'id="home-stats"' in html
    assert 'src="{{ root }}src/home-stats.js"' in html
    assert 'data-posts="{{ root }}blog/posts.json"' in html
    assert 'data-graph="{{ root }}blog/graph.json"' in html
    assert 'data-twinkles="{{ root }}twinkle/twinkles.json"' in html


def test_home_stats_module_computes_static_blog_stats():
    js = read("src/home-stats.js")
    assert "renderHomeStats" in js
    assert "buildHeatmapDays" in js
    assert "last90Days" in js
    assert "topTags" in js
    assert "twinkleCount" in js
