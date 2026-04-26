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
