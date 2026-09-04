"""
The dt view design system lives in dt_tokens.css.jinja; these tests make the
contract structural. Component styles and modules may not introduce literals
the tokens file does not sanction, and native tooltips are banned.
"""

from __future__ import annotations

import re
from pathlib import Path

COMPONENTS_DIR = Path(__file__).parent.parent / "src/deep_transcribe/resources/templates/components"
TOKENS_FILE = "dt_tokens.css.jinja"


def _css_sources() -> dict[str, str]:
    return {
        path.name: path.read_text()
        for path in COMPONENTS_DIR.glob("*.css.jinja")
        if path.name != TOKENS_FILE
    }


def _js_sources() -> dict[str, str]:
    return {path.name: path.read_text() for path in COMPONENTS_DIR.glob("*.js.jinja")}


def _strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def _declarations(css: str, prop: str) -> list[str]:
    return re.findall(rf"{prop}\s*:\s*([^;]+);", _strip_comments(css))


def test_color_literals_live_only_in_the_tokens_file() -> None:
    violations = [
        f"{name}: {match}"
        for name, css in _css_sources().items()
        for match in re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)", _strip_comments(css))
    ]
    assert not violations, f"Hex/rgb colors belong in {TOKENS_FILE}: {violations}"


def test_font_families_reference_tokens() -> None:
    violations = [
        f"{name}: {value.strip()}"
        for name, css in _css_sources().items()
        for value in _declarations(css, "font-family")
        if "var(--font-" not in value and value.strip() != "inherit"
    ]
    assert not violations, f"font-family must use the site font tokens: {violations}"


def test_radii_use_the_two_tokens() -> None:
    allowed = {"var(--dt-radius)", "var(--dt-radius-lg)", "50%", "0"}
    violations = [
        f"{name}: {value.strip()}"
        for name, css in _css_sources().items()
        for value in _declarations(css, "border-radius")
        if value.strip() not in allowed
    ]
    assert not violations, f"Only the two radius tokens (or 50%/0) are allowed: {violations}"


def test_transitions_use_duration_tokens() -> None:
    violations = [
        f"{name}: {value.strip()}"
        for name, css in _css_sources().items()
        for value in _declarations(css, "transition")
        if value.strip() != "none !important" and "var(--dt-t-" not in value
    ]
    assert not violations, f"Transitions must use the duration tokens: {violations}"


def test_shadows_use_elevation_tokens() -> None:
    violations = [
        f"{name}: {value.strip()}"
        for name, css in _css_sources().items()
        for value in _declarations(css, "box-shadow")
        if "var(--dt-shadow" not in value
        and "var(--dt-ring" not in value
        and value.strip() != "none !important"
    ]
    assert not violations, f"Shadows must use the elevation tokens: {violations}"


def test_z_indices_use_layer_tokens() -> None:
    violations = [
        f"{name}: {value.strip()}"
        for name, css in _css_sources().items()
        for value in _declarations(css, "z-index")
        if "var(--dt-z-" not in value
    ]
    assert not violations, f"Stacking must use the layer tokens: {violations}"


def test_no_native_tooltips_in_modules() -> None:
    banned = [r"\.title\s*=", r'setAttribute\(\s*"title"', r'svgEl\(\s*"title"']
    violations = [
        f"{name}: {pattern}"
        for name, js in _js_sources().items()
        for pattern in banned
        if re.search(pattern, js)
    ]
    assert not violations, (
        f"Native title tooltips are banned; use the dt_tip component: {violations}"
    )


def test_tokens_file_documents_the_system() -> None:
    tokens = (COMPONENTS_DIR / TOKENS_FILE).read_text()
    for anchor in ("TYPE", "COLOR", "TIME", "SHAPE", "PRINT", "--dt-text:", "--dt-radius:"):
        assert anchor in tokens, f"Tokens file lost its design documentation: {anchor}"
