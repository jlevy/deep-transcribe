from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from deep_transcribe.cli_main import build_legacy_parser, build_parser, main
from deep_transcribe.model_profiles import MODEL_PROFILES, ModelProvider


def test_parser_accepts_canonical_transcription_contract() -> None:
    args = build_parser().parse_args(
        [
            "transcribe",
            "--deep",
            "--no-minify",
            "--workspace",
            "./custom-workspace",
            "--language",
            "multi",
            "--rerun",
            "--json",
            "https://example.com/video",
        ]
    )

    assert args.command == "transcribe"
    assert args.deep
    assert args.no_minify
    assert args.workspace == "./custom-workspace"
    assert args.language == "multi"
    assert args.rerun
    assert args.json
    assert args.source == "https://example.com/video"


def test_legacy_parser_preserves_flag_only_contract() -> None:
    args = build_legacy_parser().parse_args(
        [
            "--deep",
            "--no_minify",
            "--workspace",
            "./custom-workspace",
            "https://example.com/video",
        ]
    )

    assert args.command == "legacy"
    assert args.deep
    assert args.no_minify
    assert args.source == "https://example.com/video"

    mcp_args = build_legacy_parser().parse_args(["--mcp"])
    assert mcp_args.mcp
    assert mcp_args.source is None


def test_help_and_model_directory_expose_all_command_surfaces() -> None:
    help_text = build_parser().format_help()

    assert all(command in help_text for command in ("transcribe", "models", "mcp", "logs"))
    assert "IMPORTANT" in help_text

    output = StringIO()
    with redirect_stdout(output):
        main(["models", "--json"])

    model_data = json.loads(output.getvalue())
    assert model_data["default"] == "anthropic"
    assert (
        model_data["profiles"]["anthropic"] == MODEL_PROFILES[ModelProvider.anthropic].as_params()
    )
    assert model_data["profiles"]["openai"] == MODEL_PROFILES[ModelProvider.openai].as_params()
    assert "4o" not in output.getvalue()


def test_model_profile_selection_persists_in_transcription_workspace() -> None:
    with TemporaryDirectory() as temp_dir:
        workspace_root = Path(temp_dir)
        output = StringIO()
        with redirect_stdout(output):
            main(
                [
                    "models",
                    "--set",
                    "openai",
                    "--json",
                    "--workspace",
                    str(workspace_root),
                ]
            )

        model_data = json.loads(output.getvalue())
        workspace_path = Path(model_data["workspace"])
        params_text = (workspace_path / ".kash/settings/params.yml").read_text()

    profile = MODEL_PROFILES[ModelProvider.openai]
    assert model_data["selected"] == "openai"
    assert f"careful_llm: {profile.careful_llm}" in params_text
    assert f"structured_llm: {profile.structured_llm}" in params_text
    assert f"standard_llm: {profile.standard_llm}" in params_text
    assert f"fast_llm: {profile.fast_llm}" in params_text


def test_cross_agent_skill_mirrors_match_distribution_source() -> None:
    repo_root = Path(__file__).parents[1]
    distribution_skill = (repo_root / "skills/deep-transcribe/SKILL.md").read_text()

    assert distribution_skill == (repo_root / ".agents/skills/deep-transcribe/SKILL.md").read_text()
    assert distribution_skill == (repo_root / ".claude/skills/deep-transcribe/SKILL.md").read_text()
    assert "deep-transcribe==0.1.6" in distribution_skill
    assert "deep-transcribe transcribe --help" in distribution_skill

    assert (repo_root / "skills/deep-transcribe/agents/openai.yaml").read_text() == (
        repo_root / ".agents/skills/deep-transcribe/agents/openai.yaml"
    ).read_text()
