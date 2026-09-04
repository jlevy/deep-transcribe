"""
The view modules ship as text inside a rendered page, so a syntax error in one is
invisible until a browser silently drops the script and a panel goes missing. Parse each
one the way the browser will.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

COMPONENTS_DIR = Path(__file__).parent.parent / "src/deep_transcribe/resources/templates/components"


def _script_paths() -> list[Path]:
    return sorted(COMPONENTS_DIR.glob("*.js.jinja"))


def test_there_are_scripts_to_check() -> None:
    assert _script_paths()


@pytest.mark.parametrize("path", _script_paths(), ids=lambda p: p.name)
def test_component_script_parses(path: Path, tmp_path: Path) -> None:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not available")
    # The modules are plain JavaScript; the .jinja suffix only marks them as template
    # includes, so node needs a name it will parse.
    copied = tmp_path / path.name.removesuffix(".jinja")
    copied.write_text(path.read_text())
    result = subprocess.run(  # noqa: S603
        [node, "--check", str(copied)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, f"{path.name} does not parse:\n{result.stderr}"
