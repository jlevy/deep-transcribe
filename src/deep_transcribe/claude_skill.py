"""
Claude Code skill installation for deep-transcribe.

Provides functionality to install the deep-transcribe skill for Claude Code,
making it available either globally across all projects or within a specific project.
"""

from __future__ import annotations

import sys
from pathlib import Path


def get_skill_content() -> str:
    """Read SKILL.md from package data.

    Returns:
        The content of the SKILL.md file as a string.

    Raises:
        ImportError: If package resources cannot be accessed.
        FileNotFoundError: If SKILL.md cannot be found in package data.
    """
    from importlib.resources import files

    skill_file = files("deep_transcribe").joinpath("skills/SKILL.md")
    return skill_file.read_text(encoding="utf-8")


def install_skill(agent_base: str | None = None) -> None:
    """Install deep-transcribe skill for Claude Code.

    Args:
        agent_base: The agent's configuration directory where skills are stored.
            - None (default): Install globally to ~/.claude/skills/deep-transcribe
            - './.claude': Install to current project's .claude/skills/deep-transcribe
            - Any path: Install to that agent base directory
    """
    if agent_base is None:
        base_dir = Path.home() / ".claude"
        location_desc = "globally"
        location_path = "~/.claude/skills/deep-transcribe"
    else:
        base_dir = Path(agent_base).resolve()
        location_desc = f"to {base_dir}"
        location_path = str(base_dir / "skills" / "deep-transcribe")

    skill_dir = base_dir / "skills" / "deep-transcribe"

    try:
        skill_content = get_skill_content()
    except (ImportError, FileNotFoundError) as e:
        print(f"\nError: Could not load skill content: {e}", file=sys.stderr)
        print(
            "\nThis command requires deep-transcribe to be installed as a package.", file=sys.stderr
        )
        print("Install with: uv tool install deep-transcribe", file=sys.stderr)
        sys.exit(1)

    try:
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(skill_content, encoding="utf-8")

        print(f"\nInstalled deep-transcribe skill {location_desc}")
        print(f"Location: {skill_file}")
        print(f"          ({location_path})")
        print("\nClaude Code will now automatically use deep-transcribe for transcription tasks.")
        print(f"To uninstall, remove this directory: {skill_dir}")

        if agent_base is not None:
            print("\nTip: Commit .claude/skills/ to share this skill with your team.")

        print()

    except PermissionError as e:
        print(f"\nPermission denied: {e}", file=sys.stderr)
        print(f"\nCould not write to {skill_dir}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"\nInstallation failed: {e}", file=sys.stderr)
        sys.exit(1)
