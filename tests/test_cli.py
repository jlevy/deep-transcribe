from __future__ import annotations

import json
import os
import subprocess
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

import pytest

from deep_transcribe.cli_main import (
    build_direct_parser,
    build_parser,
    build_transcription_metadata,
    configure_kash_workspace,
    main,
)
from deep_transcribe.model_profiles import MODEL_PROFILES, ModelProvider


def test_help_path_does_not_import_runtime_stack() -> None:
    code = """
import sys
from deep_transcribe.cli_main import build_parser

build_parser().format_help()
heavy_modules = sorted(
    name
    for name in sys.modules
    if name == "kash"
    or name.startswith("kash.")
    or name == "clideps"
    or name.startswith("clideps.")
)
if heavy_modules:
    raise RuntimeError(f"Help imported runtime modules: {heavy_modules}")
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )

    assert not result.stderr


def test_keyboard_interrupt_exits_without_traceback() -> None:
    code = dedent("""
        import os
        import signal

        from deep_transcribe import cli_main

        def interrupt(argv):
            os.kill(os.getpid(), signal.SIGINT)

        cli_main._run_cli = interrupt
        raise SystemExit(cli_main.main([]))
        """)
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 130
    assert result.stdout == ""
    assert result.stderr == "\nInterrupted.\n"
    assert "Traceback" not in result.stderr


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
            "--rerun-processing",
            "--json",
            "--key-term",
            "SignalFlow",
            "--speaker",
            "0=Alice Chen",
            "--speaker-role",
            "Alice Chen",
            "--speaker-role",
            "Bob Diaz",
            "--instructions",
            "Use a concise section-aligned outline.",
            "https://example.com/video",
        ]
    )

    assert args.command == "transcribe"
    assert args.deep
    assert args.no_minify
    assert args.workspace == "./custom-workspace"
    assert args.language == "multi"
    assert args.rerun
    assert args.rerun_processing
    assert args.json
    assert args.key_term == ["SignalFlow"]
    assert args.speaker == [("0", "Alice Chen")]
    assert args.speaker_role == ["Alice Chen", "Bob Diaz"]
    assert args.instructions == ["Use a concise section-aligned outline."]
    assert args.transcription_model == "nova-3"
    assert args.diarize_model == "latest"
    assert args.source == "https://example.com/video"


def test_transcribe_help_explains_incremental_and_forced_reruns() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "deep_transcribe", "transcribe", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    help_text = " ".join(result.stdout.split())

    assert "normal rerun resumes at the first affected stage" in help_text
    assert "--rerun-processing" in help_text
    assert "forces every post-transcription stage" in help_text
    assert "--rerun" in help_text
    assert "including speech-to-text" in help_text
    assert "--instructions" in help_text
    assert "Trusted post-transcription processing instructions" in help_text


def test_cli_metadata_file_and_inline_values_merge() -> None:
    with TemporaryDirectory() as temp_dir:
        metadata_path = Path(temp_dir) / "interview.yml"
        metadata_path.write_text(
            dedent("""
                description: Product interview
                additional_context: Old context
                processing_instructions: Prefer sections from the transcript.
                key_terms: [SignalFlow]
                speaker_hints: {0: Alice Chen}
                speaker_roster: [Alice Chen, Bob Diaz]
                """).strip()
        )
        args = build_parser().parse_args(
            [
                "transcribe",
                "--metadata",
                str(metadata_path),
                "--context",
                "Alice interviews Bob.",
                "--key-term",
                "Nova Prime",
                "--speaker",
                "1=Bob Diaz",
                "--speaker-role",
                "Carol Evans",
                "--instructions",
                "Keep each section concise.",
                "https://example.com/video",
            ]
        )
        metadata = build_transcription_metadata(args)

    assert metadata.description == "Product interview"
    assert metadata.additional_context == "Alice interviews Bob."
    assert metadata.key_terms == ["SignalFlow", "Nova Prime"]
    assert metadata.extra["transcription"]["speaker_hints"] == {
        "0": "Alice Chen",
        "1": "Bob Diaz",
    }
    assert metadata.speaker_roster == ["Alice Chen", "Bob Diaz", "Carol Evans"]
    assert metadata.processing_instructions == (
        "Prefer sections from the transcript.\n\nKeep each section concise."
    )


def test_direct_parser_supports_the_concise_transcription_contract() -> None:
    args = build_direct_parser().parse_args(
        [
            "--deep",
            "--no_minify",
            "--workspace",
            "./custom-workspace",
            "https://example.com/video",
        ]
    )

    assert args.command == "transcribe"
    assert args.deep
    assert args.no_minify
    assert args.source == "https://example.com/video"


def test_kash_workspace_is_configured_before_runtime_imports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("KASH_WS_ROOT", raising=False)

    workspace = configure_kash_workspace(tmp_path / "transcriptions")

    assert workspace == (tmp_path / "transcriptions").resolve()
    assert workspace == Path(os.environ["KASH_WS_ROOT"])


def test_help_and_model_directory_expose_all_command_surfaces() -> None:
    help_text = build_parser().format_help()

    assert all(command in help_text for command in ("transcribe", "models"))
    assert "mcp" not in help_text.lower()
    assert "logs" not in help_text.lower()
    assert "--docs" in help_text
    assert "--skill" in help_text
    assert "--install-skill" in help_text
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


def test_docs_and_skill_cli_paths_avoid_the_runtime_stack() -> None:
    for option, expected in (
        ("--docs", "Iterate Without Repeating Speech-to-Text"),
        ("--skill", "name: deep-transcribe"),
    ):
        result = subprocess.run(
            [sys.executable, "-m", "deep_transcribe", option],
            check=True,
            capture_output=True,
            text=True,
        )
        assert expected in result.stdout
        assert "MCP" not in result.stdout


def test_install_skill_cli_validates_surface_arguments(tmp_path: Path) -> None:
    assert main(["--install-skill", "--agent-base", str(tmp_path / "agent")]) is None
    assert (tmp_path / "agent/skills/deep-transcribe/SKILL.md").is_file()

    with pytest.raises(SystemExit) as error:
        main(["--install-skill", "--surfaces=portable", "--agent-base", str(tmp_path)])
    assert error.value.code == 2

    with pytest.raises(SystemExit) as error:
        main(["--install-skill", "--surfaces=unknown"])
    assert error.value.code == 2

    with pytest.raises(SystemExit) as error:
        main(["--install-skill", "--surfaces="])
    assert error.value.code == 2

    with pytest.raises(SystemExit) as error:
        main(["--agent-base", str(tmp_path)])
    assert error.value.code == 2


@pytest.mark.parametrize("arguments", [["mcp"], ["logs"], ["--mcp"], ["--sse"], ["--logs"]])
def test_removed_mcp_surfaces_are_rejected(arguments: list[str]) -> None:
    with pytest.raises(SystemExit) as error:
        main(arguments)

    assert error.value.code == 2
