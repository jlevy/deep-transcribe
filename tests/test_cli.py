from __future__ import annotations

import json
import os
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from kash.model import Item

from deep_transcribe.cli_main import (
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


def test_single_help_page_explains_incremental_and_forced_reruns() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "deep_transcribe", "--help"],
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
    assert "ordinary prose" in help_text
    assert "Optional structured overrides for automation" in help_text
    assert "Commands:" not in result.stdout
    assert "deep-transcribe transcribe" not in result.stdout
    assert "deep-transcribe models" not in result.stdout
    assert "--models [PROFILE]" in result.stdout
    assert result.stdout.index("--context TEXT") < result.stdout.index("--metadata YAML_OR_JSON")


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
                "--metadata",
                str(metadata_path),
                "--title",
                "Updated product conversation",
                "--description",
                "Alice and Bob discuss the product roadmap.",
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

    assert metadata.title == "Updated product conversation"
    assert metadata.description == "Alice and Bob discuss the product roadmap."
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


def test_parser_supports_the_direct_transcription_contract() -> None:
    args = build_parser().parse_args(
        [
            "--deep",
            "--no_minify",
            "--workspace",
            "./custom-workspace",
            "--title",
            "Product conversation",
            "--description",
            "Alice discusses the roadmap with Bob.",
            "--context",
            "Alice hosts and Bob presents.",
            "https://example.com/video",
        ]
    )

    assert args.deep
    assert args.no_minify
    assert args.title == "Product conversation"
    assert args.description == "Alice discusses the roadmap with Bob."
    assert args.context == ["Alice hosts and Bob presents."]
    assert args.source == "https://example.com/video"


def test_kash_workspace_is_configured_before_runtime_imports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("KASH_WS_ROOT", raising=False)

    workspace = configure_kash_workspace(tmp_path / "transcriptions")

    assert workspace == (tmp_path / "transcriptions").resolve()
    assert workspace == Path(os.environ["KASH_WS_ROOT"])


def test_help_and_models_flag_expose_all_surfaces(tmp_path: Path) -> None:
    help_text = build_parser().format_help()

    assert "mcp" not in help_text.lower()
    assert "logs" not in help_text.lower()
    assert "--docs" in help_text
    assert "--skill" in help_text
    assert "--install-skill" in help_text
    assert "--models [PROFILE]" in help_text

    output = StringIO()
    with redirect_stdout(output):
        main(["--models", "--json", "--workspace", str(tmp_path)])

    model_data = json.loads(output.getvalue())
    assert model_data["default"] == "anthropic"
    assert model_data["active"] == "anthropic"
    assert model_data["workspace"] == str((tmp_path / "workspace").resolve())
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
                    "--models",
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


def test_models_profile_can_be_selected_before_transcription(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from kash.config import setup

    from deep_transcribe import transcribe_commands

    source = "https://example.com/video"
    observed: dict[str, object] = {}

    def fake_kash_setup(**_kwargs: object) -> None:
        pass

    def fake_run_transcription(
        base_dir: Path,
        source_arg: str,
        *_args: object,
        **_kwargs: object,
    ) -> tuple[Path, Path]:
        profile = MODEL_PROFILES[ModelProvider.openai]
        params_text = (base_dir / "workspace/.kash/settings/params.yml").read_text(encoding="utf-8")
        observed["source"] = source_arg
        observed["profile_saved"] = f"careful_llm: {profile.careful_llm}" in params_text
        return base_dir / "transcript.md", base_dir / "transcript.html"

    monkeypatch.setattr(transcribe_commands, "run_transcription", fake_run_transcription)
    monkeypatch.setattr(setup, "kash_setup", fake_kash_setup)
    # kash_setup is mocked, so no .env loading happens; satisfy the key preflight.
    monkeypatch.setenv("DEEPGRAM_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    output = StringIO()
    with redirect_stdout(output):
        main(
            [
                "--models",
                "openai",
                "--workspace",
                str(tmp_path),
                "--json",
                source,
            ]
        )

    assert observed == {"source": source, "profile_saved": True}
    assert json.loads(output.getvalue())["html"].endswith("transcript.html")


def test_models_flag_reports_invalid_workspace_settings_without_a_traceback(
    tmp_path: Path,
) -> None:
    params_path = tmp_path / "workspace/.kash/settings/params.yml"
    params_path.parent.mkdir(parents=True)
    params_path.write_text("- not-a-settings-mapping\n", encoding="utf-8")

    errors = StringIO()
    with redirect_stderr(errors), pytest.raises(SystemExit) as error:
        main(["--models", "--workspace", str(tmp_path)])

    assert error.value.code == 2
    assert "Invalid workspace model settings" in errors.getvalue()
    assert "Traceback" not in errors.getvalue()


def test_source_is_required_unless_an_early_action_was_requested(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as error:
        main(["--deep"])
    assert error.value.code == 2

    with pytest.raises(SystemExit) as error:
        main(["https://example.com/video", "--models"])
    assert error.value.code == 2

    assert main(["--models", "--workspace", str(tmp_path)]) is None


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


@pytest.mark.parametrize("arguments", [["--mcp"], ["--sse"], ["--logs"]])
def test_removed_mcp_options_are_rejected(arguments: list[str]) -> None:
    with pytest.raises(SystemExit) as error:
        main(arguments)

    assert error.value.code == 2


@pytest.mark.parametrize("source", ["transcribe", "models", "mcp", "logs"])
def test_former_command_names_are_plain_sources(source: str) -> None:
    assert build_parser().parse_args([source]).source == source


def test_cli_golden_keeps_the_version_placeholder() -> None:
    """
    `tryscript run --update` bakes the local dev version into the golden, and CI
    then fails on its own commit hash. The frontmatter VERSION pattern exists to
    normalize it, so fail here instead of in CI.
    """
    import re
    from pathlib import Path as _Path

    golden = _Path(__file__).parent / "tryscript" / "cli.tryscript.md"
    text = golden.read_text()

    assert "deep-transcribe v[VERSION]" in text
    assert not re.search(r"deep-transcribe v\d+\.\d+\.\d+", text), (
        "A literal version was baked into the CLI golden; restore v[VERSION]."
    )


def test_results_point_at_the_suggested_hints_beside_the_transcript(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    The suggestion is written into the kash workspace, which sits one level inside the
    root the user passed on the command line. Checking the wrong one means a detected
    highlight reel is found and then never mentioned.
    """
    from deep_transcribe.cli_main import display_results
    from deep_transcribe.transcribe_commands import SUGGESTED_SEGMENTS_NAME

    root = tmp_path / "run"
    workspace = root / "workspace"
    docs = workspace / "docs"
    docs.mkdir(parents=True)
    transcript = docs / "t.doc.md"
    transcript.write_text("x")
    html = workspace / "exports" / "t.html"
    html.parent.mkdir(parents=True)
    html.write_text("<html></html>")
    (workspace / SUGGESTED_SEGMENTS_NAME).write_text("segments: []\n")

    display_results(root, transcript, html, as_json=True)

    import json as _json

    payload = _json.loads(capsys.readouterr().out)
    assert payload["suggested_segments"] == str((workspace / SUGGESTED_SEGMENTS_NAME).resolve())


def test_results_omit_the_hint_path_when_nothing_was_suggested(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from deep_transcribe.cli_main import display_results

    root = tmp_path / "run"
    docs = root / "workspace" / "docs"
    docs.mkdir(parents=True)
    transcript = docs / "t.doc.md"
    transcript.write_text("x")
    html = root / "workspace" / "exports" / "t.html"
    html.parent.mkdir(parents=True)
    html.write_text("<html></html>")

    display_results(root, transcript, html, as_json=True)

    import json as _json

    assert "suggested_segments" not in _json.loads(capsys.readouterr().out)


def test_segments_flag_survives_metadata_validation(tmp_path: Path) -> None:
    """
    --segments was built, documented, and never run end to end. The metadata validator
    rejects unknown fields, so the flag failed on the first real invocation with
    "Unsupported transcription metadata fields: ['segments']" before anything ran.
    """
    import argparse

    from kash.model import Item, ItemType

    from deep_transcribe.cli_main import build_transcription_metadata
    from deep_transcribe.transcription_metadata import get_segment_hints

    hints = tmp_path / "segments.yml"
    hints.write_text('segments:\n  - at: "0:00 - 1:49"\n    purpose: teaser\n')

    args = argparse.Namespace(
        metadata=None,
        context_file=[],
        context=[],
        segments=hints,
        title=None,
        description=None,
        key_term=[],
        speaker=None,
        speaker_role=None,
        instructions_file=[],
        instructions=[],
    )

    metadata = build_transcription_metadata(args)

    item = Item(type=ItemType.doc, body="x", extra=metadata.extra)
    carried = get_segment_hints(item)
    assert isinstance(carried, dict)
    assert carried["segments"][0]["purpose"] == "teaser"
    assert carried["segments"][0]["at"] == "0:00:00 - 0:01:49"


def test_a_bad_hints_file_is_a_usage_error_not_a_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    A mistake in a file the user wrote is a usage error. Reached through the generic
    runtime handler instead, an unknown purpose printed a full traceback into our own
    parser before the readable line, which is not a message anyone reads.
    """
    from kash.config import setup

    from deep_transcribe import transcribe_commands

    hints = tmp_path / "segments.yml"
    hints.write_text('segments:\n  - at: "0:00 - 0:20"\n    purpose: cold_open\n')

    def unreachable(*_args: object, **_kwargs: object) -> tuple[Path, Path]:
        raise AssertionError("the run must not start with an unreadable hints file")

    def fake_kash_setup(**_kwargs: object) -> None:
        pass

    monkeypatch.setattr(transcribe_commands, "run_transcription", unreachable)
    monkeypatch.setattr(setup, "kash_setup", fake_kash_setup)
    monkeypatch.setenv("DEEPGRAM_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    errors = StringIO()
    with redirect_stderr(errors), pytest.raises(SystemExit) as error:
        main(
            [
                "--basic",
                "--workspace",
                str(tmp_path),
                "--segments",
                str(hints),
                "https://example.com/video",
            ]
        )

    assert error.value.code == 2
    reported = errors.getvalue()
    assert "cold_open" in reported
    assert "teaser, intro, promo, outro, other" in reported
    assert "Traceback" not in reported


def test_metadata_still_rejects_a_genuinely_unknown_field() -> None:
    from deep_transcribe.transcription_metadata import transcription_metadata_from_mapping

    with pytest.raises(ValueError, match="Unsupported"):
        transcription_metadata_from_mapping({"not_a_field": 1})


def _item_with_stored_guidance() -> Item:
    """A source item shaped like one a previous run left hints and instructions on."""
    from kash.model import Item, ItemType

    from deep_transcribe.transcription_metadata import set_segment_hints

    item = Item(
        type=ItemType.resource,
        extra={
            "transcription": {
                "key_terms": ["SignalFlow"],
                "speaker_roster": ["Host", "Guest"],
                "processing_instructions": "Emphasize the open questions.",
            }
        },
    )
    set_segment_hints(item, {"segments": [{"at": "0:00:00 - 0:01:49", "purpose": "teaser"}]})
    return item


def _stored_transcription(item: Item) -> dict[str, object]:
    assert item.extra is not None
    transcription = item.extra["transcription"]
    assert isinstance(transcription, dict)
    return transcription


def test_segments_none_clears_stored_hints() -> None:
    """
    Hints are written back onto the stored source so a later run keeps honoring them,
    which leaves a user who marked a teaser and now wants it back with no way out but
    editing the workspace YAML by hand.
    """
    from deep_transcribe.transcription_metadata import (
        apply_transcription_metadata,
        get_segment_hints,
    )

    args = build_parser().parse_args(["--segments", "none", "https://example.com/video"])
    metadata = build_transcription_metadata(args)
    item = _item_with_stored_guidance()
    assert get_segment_hints(item) is not None

    apply_transcription_metadata(item, metadata)

    assert metadata.clear_segments is True
    assert get_segment_hints(item) is None
    assert "segments" not in _stored_transcription(item)


def test_instructions_none_clears_stored_instructions() -> None:
    from deep_transcribe.transcription_metadata import (
        apply_transcription_metadata,
        get_processing_instructions,
    )

    args = build_parser().parse_args(["--instructions", "NONE", "https://example.com/video"])
    metadata = build_transcription_metadata(args)
    item = _item_with_stored_guidance()
    assert get_processing_instructions(item) == "Emphasize the open questions."

    apply_transcription_metadata(item, metadata)

    assert metadata.clear_processing_instructions is True
    assert get_processing_instructions(item) is None
    assert "processing_instructions" not in _stored_transcription(item)


def test_clearing_leaves_the_rest_of_the_stored_transcription_metadata_alone() -> None:
    """A clear must remove exactly one key, not reset the source's other guidance."""
    from deep_transcribe.transcription_metadata import apply_transcription_metadata

    args = build_parser().parse_args(
        ["--segments", "none", "--instructions", "none", "https://example.com/video"]
    )
    metadata = build_transcription_metadata(args)
    item = _item_with_stored_guidance()

    apply_transcription_metadata(item, metadata)

    assert item.extra == {
        "transcription": {
            "key_terms": ["SignalFlow"],
            "speaker_roster": ["Host", "Guest"],
        }
    }


def test_a_segments_file_path_is_still_read_as_a_path(tmp_path: Path) -> None:
    """`none` is a literal, so an ordinary hints file must be unaffected by it."""
    from deep_transcribe.transcription_metadata import (
        apply_transcription_metadata,
        get_segment_hints,
    )

    hints = tmp_path / "segments.yml"
    hints.write_text('segments:\n  - at: "0:00 - 1:49"\n    purpose: promo\n')

    args = build_parser().parse_args(
        ["--segments", str(hints), "--instructions", "Keep it short.", "https://example.com/video"]
    )
    metadata = build_transcription_metadata(args)
    item = _item_with_stored_guidance()

    apply_transcription_metadata(item, metadata)

    assert metadata.clear_segments is False
    assert metadata.clear_processing_instructions is False
    carried = get_segment_hints(item)
    assert isinstance(carried, dict)
    assert carried["segments"][0]["purpose"] == "promo"
    assert _stored_transcription(item)["processing_instructions"] == "Keep it short."
