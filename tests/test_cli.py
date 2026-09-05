from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import TYPE_CHECKING, override

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


def test_replace_flags_merge_with_the_metadata_file_and_win_on_conflict() -> None:
    with TemporaryDirectory() as temp_dir:
        metadata_path = Path(temp_dir) / "recipe.yml"
        metadata_path.write_text(
            dedent("""
                replacements:
                  Omachi: Omarchy
                  Hansen: Hanson
                """).strip()
        )
        args = build_parser().parse_args(
            [
                "--metadata",
                str(metadata_path),
                "--replace",
                "Hansen=Hansson",
                "--replace",
                "Amache=Omarchy",
                "https://example.com/video",
            ]
        )
        metadata = build_transcription_metadata(args)

    assert args.replace == [("Hansen", "Hansson"), ("Amache", "Omarchy")]
    # The file's own entry survives, the new one is added, and the flag wins where both
    # name the same misheard word.
    assert metadata.replacements == {
        "Omachi": "Omarchy",
        "Hansen": "Hansson",
        "Amache": "Omarchy",
    }


def test_a_replace_flag_without_an_equals_sign_is_a_usage_error() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--replace", "Omachi", "https://example.com/video"])


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
    from deep_transcribe.transcribe_commands import TranscriptionOutputs

    source = "https://example.com/video"
    observed: dict[str, object] = {}

    def fake_kash_setup(**_kwargs: object) -> None:
        pass

    def fake_run_transcription(
        base_dir: Path,
        source_arg: str,
        *_args: object,
        **_kwargs: object,
    ) -> TranscriptionOutputs:
        profile = MODEL_PROFILES[ModelProvider.openai]
        params_text = (base_dir / "workspace/.kash/settings/params.yml").read_text(encoding="utf-8")
        observed["source"] = source_arg
        observed["profile_saved"] = f"careful_llm: {profile.careful_llm}" in params_text
        return TranscriptionOutputs(base_dir / "transcript.md", base_dir / "transcript.html")

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
        replace=[],
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


class _Recorder(logging.Handler):
    """Every record the root logger sees, so what kash's handlers do with them is testable."""

    def __init__(self) -> None:
        super().__init__(level=logging.NOTSET)
        self.records: list[logging.LogRecord] = []

    @override
    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _console_text(records: list[logging.LogRecord]) -> str:
    """
    What the console would have shown, formatted the way a handler formats.

    kash puts its console handler at warning level and its file handler at info, so records
    below warning never reach the terminal. `Formatter.format` appends the traceback when a
    record carries `exc_info`, which is exactly how a stack dump got in front of the user.
    """
    formatter = logging.Formatter("%(levelname)s %(message)s")
    return "\n".join(formatter.format(r) for r in records if r.levelno >= logging.WARNING)


def _drive_main_through_a_failed_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: BaseException,
) -> tuple[int | None, str, list[logging.LogRecord]]:
    """
    Reach the top-level handler with a chosen failure and report everything it produced.

    kash setup is faked so the run never touches the real workspace machinery. Logging is
    watched with an own handler rather than `caplog` because importing kash replaces the
    root handlers, pytest's capture among them — which is also why an assertion on
    redirected stderr alone would prove nothing about the traceback.
    """
    from kash.config import setup

    from deep_transcribe import transcribe_commands

    def failing_run(*_args: object, **_kwargs: object) -> tuple[Path, Path]:
        raise failure

    def fake_kash_setup(**_kwargs: object) -> None:
        pass

    monkeypatch.setattr(transcribe_commands, "run_transcription", failing_run)
    monkeypatch.setattr(setup, "kash_setup", fake_kash_setup)
    monkeypatch.setenv("DEEPGRAM_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    recorder = _Recorder()
    root = logging.getLogger()
    root.addHandler(recorder)
    previous_level = root.level
    root.setLevel(logging.DEBUG)
    out, err = StringIO(), StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err), pytest.raises(SystemExit) as exit_info:
            main(["--basic", "--workspace", str(tmp_path), "https://example.com/video"])
    finally:
        root.removeHandler(recorder)
        root.setLevel(previous_level)

    code = exit_info.value.code
    assert isinstance(code, int) or code is None
    # Rich wraps to the console width, so compare on collapsed whitespace rather than on
    # wherever the terminal happened to break the sentence.
    reported = " ".join((out.getvalue() + err.getvalue()).split())
    return code, reported, recorder.records


def test_a_disk_space_stop_is_one_line_and_not_a_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    The run this check exists for ended in a raw traceback followed by a friendly line.
    A two-hour run that ends in a stack dump buries the one sentence that says what to do,
    so the preflight's message has to arrive on its own.

    Both halves matter. The console must carry the sentence and no traceback, and the
    traceback must still be recorded for the log file the message points at — dropping it
    would trade one lost diagnostic for another.
    """
    from deep_transcribe.disk_space import InsufficientDiskSpace

    stop = InsufficientDiskSpace(
        "Not enough free space on /Volumes/Backup to download this source: "
        "about 4.2 GB needed for a 5h15m recording, 1.1 GB free. "
        "Free space or use --workspace on another volume."
    )

    code, reported, records = _drive_main_through_a_failed_run(tmp_path, monkeypatch, stop)

    assert code != 0
    assert "Not enough free space on /Volumes/Backup to download this source:" in reported
    assert "about 4.2 GB needed for a 5h15m recording, 1.1 GB free." in reported
    assert "--workspace on another volume" in reported

    console = _console_text(records)
    assert "Traceback" not in console, f"the console still dumps a traceback:\n{console}"
    assert any(r.exc_info for r in records), (
        "the traceback was dropped entirely; it must still reach the log file"
    )
    assert "Error: Not enough" not in reported, f"double-labelled the message: {reported}"


def _mapped_failure_reaches_the_console(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: BaseException,
) -> tuple[int | None, str, str]:
    """Drive `main()` through one mapped failure, returning the exit code, console, and log."""
    code, reported, records = _drive_main_through_a_failed_run(tmp_path, monkeypatch, failure)
    return code, reported, _console_text(records)


def test_a_disk_full_download_reports_the_disk_and_not_the_video(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    The reported run: twenty minutes of downloading, then a yt-dlp `UnavailableVideoError`
    traceback ending in `[Errno 28] No space left on device`, then a friendly line. The
    outer exception blames the video; only the cause is actionable.
    """
    import errno

    from yt_dlp.utils import UnavailableVideoError

    try:
        try:
            raise OSError(errno.ENOSPC, "No space left on device", str(tmp_path / "v.mp4.part"))
        except OSError as cause:
            raise UnavailableVideoError("Video unavailable") from cause
    except UnavailableVideoError as error:
        code, reported, console = _mapped_failure_reaches_the_console(tmp_path, monkeypatch, error)

    assert code != 0
    assert "Ran out of space on " in reported, reported
    assert "Free space or use --workspace on another volume." in reported, reported
    assert "private" not in reported, f"blamed the video for a full disk: {reported}"
    assert "Traceback" not in console, f"the console still dumps a traceback:\n{console}"


def test_a_download_failure_names_the_url_and_what_to_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from yt_dlp.utils import DownloadError

    failure = DownloadError("ERROR: [youtube] abc: Video unavailable")
    code, reported, console = _mapped_failure_reaches_the_console(tmp_path, monkeypatch, failure)

    assert code != 0
    assert "Could not download https://example.com/video:" in reported, reported
    assert "Video unavailable." in reported, reported
    assert "private/geo-blocked" in reported, reported
    assert "Traceback" not in console, f"the console still dumps a traceback:\n{console}"


def test_an_extractor_failure_is_one_line_without_the_bug_report_paragraph(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    yt-dlp asks the user to file a github issue for a private video. Passing that through
    sends people to the wrong repository for a problem only they can fix.
    """
    from yt_dlp.utils import ExtractorError

    failure = ExtractorError("Private video. Sign in if you have been granted access", video_id="a")
    code, reported, console = _mapped_failure_reaches_the_console(tmp_path, monkeypatch, failure)

    assert code != 0
    assert "Private video. Sign in if you have been granted access." in reported, reported
    assert "github.com/yt-dlp" not in reported, reported
    assert "Traceback" not in console, f"the console still dumps a traceback:\n{console}"


def test_a_network_failure_names_the_host_it_could_not_reach(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    kash fetches with httpx, so a connection failure arrives as a `TransportError` carrying
    the request it was making — which is the only place the host is written down.
    """
    import httpx

    request = httpx.Request("GET", "https://rr3---sn-x.googlevideo.com/videoplayback?id=1")
    failure = httpx.ConnectError("[Errno 8] nodename nor servname provided", request=request)
    code, reported, console = _mapped_failure_reaches_the_console(tmp_path, monkeypatch, failure)

    assert code != 0
    assert "Could not reach rr3---sn-x.googlevideo.com:" in reported, reported
    assert "Check your network connection and try again." in reported, reported
    assert "Traceback" not in console, f"the console still dumps a traceback:\n{console}"


def test_an_unmapped_failure_still_gets_the_traceback_it_always_had(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    The point of mapping is not to quieten failures, it is to explain the ones understood.
    A structural bug in this codebase has no actionable one-liner, so nothing about its
    reporting changes — and if this ever passes by accident, the mapping has grown too eager.
    """
    failure = ValueError("something structural went wrong")
    code, reported, console = _mapped_failure_reaches_the_console(tmp_path, monkeypatch, failure)

    assert code != 0
    assert "Error: something structural went wrong" in reported, reported
    assert "Traceback" in console, f"an unknown failure lost its traceback:\n{console}"


EXPORTED_SOURCE = "https://example.com/exported-recording"
"""The source the stored item claims, so the re-export has something to match it against."""


def _exported_body() -> str:
    """
    A final item's body, small but shaped like a real one: the structures the report counts
    and nothing else. Two `##` sections, two labelled turns anchored by the citation spans
    the pipeline emits, an outline block, and one name spelled two ways.
    """

    def turn(label: str, ts: str, text: str) -> str:
        chip = (
            f'<span class="citation timestamp-link" data-src="r.yml" '
            f'data-timestamp="{ts}">{ts}</span>'
        )
        return f"**{label}:** {text} {chip}\n\n"

    return (
        '<div class="transcript-outline" style="x">\n\n'
        "- **Opening**\n- **The setup**\n\n"
        '<div class="original">\n\n</div>\n\n'
        "## Opening\n\n"
        + turn("Ada", "12.50", "We are talking about Omarchy today.")
        + "## The setup\n\n"
        + turn("Grace", "600.25", "Omachi is the spelling on the box.")
    )


def _exported_item() -> Item:
    """The item a finished run hands `format_results`, with its analysis attached."""
    from kash.model import Format, Item, ItemType
    from kash.utils.common.url import Url

    return Item(
        type=ItemType.doc,
        format=Format.md_html,
        title="A finished recording",
        url=Url(EXPORTED_SOURCE),
        body=_exported_body(),
        extra={
            # Half an hour makes the per-hour density checkable by eye.
            "duration": 1800,
            "transcription": {
                "concepts": [
                    {"name": "Omarchy", "theme": "Tooling", "mentions": ["12.50"]},
                    {"name": "Linux", "theme": "Tooling", "mentions": ["600.25"]},
                    {"name": "An aside", "mentions": ["12.50"]},
                ]
            },
        },
    )


def test_report_is_folded_into_the_json_a_run_prints(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    `--report --json` has to stay one parseable document.

    An agent driving the loop reads the JSON with a single parse, so the report belongs
    under a key beside the paths rather than printed next to them. This also pins that
    `--report` actually reaches the run, which is the half a report-shaped dict cannot
    prove on its own.
    """
    from kash.config import setup

    from deep_transcribe import transcribe_commands
    from deep_transcribe.transcribe_commands import TranscriptionOutputs
    from deep_transcribe.transcript_report import build_transcript_report

    observed: dict[str, object] = {}

    def fake_kash_setup(**_kwargs: object) -> None:
        pass

    def fake_run_transcription(
        base_dir: Path, _source: str, *_args: object, **kwargs: object
    ) -> TranscriptionOutputs:
        observed["report_requested"] = kwargs.get("report")
        return TranscriptionOutputs(
            base_dir / "transcript.md",
            base_dir / "transcript.html",
            # Built by the real builder over a real item: the CLI's job is to carry and
            # render this, and a hand-written stub would test the test.
            report=build_transcript_report(_exported_item()),
        )

    monkeypatch.setattr(transcribe_commands, "run_transcription", fake_run_transcription)
    monkeypatch.setattr(setup, "kash_setup", fake_kash_setup)
    monkeypatch.setenv("DEEPGRAM_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    output = StringIO()
    with redirect_stdout(output):
        main(["--workspace", str(tmp_path), "--report", "--json", EXPORTED_SOURCE])

    assert observed == {"report_requested": True}

    payload = json.loads(output.getvalue())
    assert payload["html"].endswith("transcript.html")
    report = payload["report"]
    assert sorted(report) == [
        "duration",
        "frames",
        "headings",
        "outline",
        "segments",
        "speakers",
        "spellings",
        "themes",
    ]
    assert report["headings"]["count"] == 2
    # Two sections in half an hour.
    assert report["headings"]["per_hour"] == 4.0
    assert [h["title"] for h in report["headings"]["list"]] == ["Opening", "The setup"]
    assert report["outline"]["entries"] == 2
    assert report["themes"] == {
        "count": 1,
        "unthemed_concepts": 1,
        "list": [{"name": "Tooling", "concepts": 2}],
    }
    assert [(s["label"], s["turns"]) for s in report["speakers"]] == [("Ada", 1), ("Grace", 1)]
    spelled = {row["token"] for row in report["spellings"]}
    assert {"Omarchy", "Omachi"} <= spelled


def _store_a_finished_run(ws_root: Path) -> Path:
    """
    Leave in the workspace what a finished run leaves: one exported doc item for the source.

    Written through kash rather than as a file so the frontmatter is whatever a real save
    produces, which is what the re-export's lookup reads.
    """
    from kash.exec import kash_runtime
    from kash.workspaces import current_ws

    with kash_runtime(ws_root / "workspace"):
        item = _exported_item()
        current_ws().save(item)
        assert item.store_path
        return ws_root / "workspace" / str(item.store_path)


def test_export_only_rebuilds_the_page_from_the_cached_item_and_runs_no_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    The flag exists for a template or `--elements` change: the analysis is done and only
    the rendering moved. So the whole pipeline must stay untouched — every stage entry the
    CLI can reach is booby-trapped here — while a real page still comes out the other end,
    written by the same `format_results` a normal run ends with.

    Nothing is mocked on the way out. The HTML is rendered for real from the stored item,
    which is also the only way to catch a re-export that finds an item it cannot render.
    """
    from deep_transcribe import transcribe_commands

    stored = _store_a_finished_run(tmp_path)
    stored_before = stored.read_bytes()

    def no_stage_may_run(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("--export-only ran a pipeline stage")

    monkeypatch.setattr(transcribe_commands, "run_transcription", no_stage_may_run)
    monkeypatch.setattr(transcribe_commands, "transcribe_with_options", no_stage_may_run)
    monkeypatch.setattr(transcribe_commands, "_process_transcript", no_stage_may_run)
    # A re-export calls no service, so it must not even ask for a key.
    monkeypatch.delenv("DEEPGRAM_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    output = StringIO()
    with redirect_stdout(output):
        main(
            [
                "--workspace",
                str(tmp_path),
                "--export-only",
                "--report",
                "--json",
                EXPORTED_SOURCE,
            ]
        )

    payload = json.loads(output.getvalue())
    html_path = Path(payload["html"])
    assert html_path.exists(), f"--export-only reported HTML that is not there: {html_path}"
    assert html_path.suffix == ".html"
    html = html_path.read_text(encoding="utf-8")
    assert "A finished recording" in html
    assert "Omarchy" in html
    # `--report --export-only` reports over the item it re-exported.
    assert payload["report"]["headings"]["count"] == 2
    assert payload["transcript"] == str(stored.resolve())
    assert stored.read_bytes() == stored_before, "the re-export rewrote the item it read"

    # The text form prints the report first, so the paths stay the last thing on screen.
    text_output = StringIO()
    with redirect_stdout(text_output):
        main(["--workspace", str(tmp_path), "--export-only", "--report", EXPORTED_SOURCE])

    printed = text_output.getvalue()
    assert "headings 2 (4.0/h)" in printed
    assert printed.index("headings 2") < printed.index("All done!")


def test_export_only_without_a_prior_run_is_a_usage_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    The mistyped workspace or source, which is the likely way to reach this flag wrongly.
    The answer is argparse's one line and exit 2 — not a traceback, and not an empty page
    that looks like a successful re-export.
    """
    monkeypatch.delenv("DEEPGRAM_API_KEY", raising=False)

    errors = StringIO()
    with redirect_stderr(errors), pytest.raises(SystemExit) as raised:
        main(["--workspace", str(tmp_path), "--export-only", EXPORTED_SOURCE])

    assert raised.value.code == 2
    reported = errors.getvalue()
    error_lines = [line for line in reported.splitlines() if "error:" in line]
    assert len(error_lines) == 1, f"expected one error line, got:\n{reported}"
    assert EXPORTED_SOURCE in error_lines[0]
    assert "--export-only" in error_lines[0]
    assert "Traceback" not in reported


def test_export_only_refuses_to_be_combined_with_a_rerun(tmp_path: Path) -> None:
    """`--rerun` asks for stages to run and `--export-only` asks for none to; say so."""
    for rerun_flag in ("--rerun", "--rerun-processing"):
        errors = StringIO()
        with redirect_stderr(errors), pytest.raises(SystemExit) as raised:
            main(["--workspace", str(tmp_path), "--export-only", rerun_flag, EXPORTED_SOURCE])

        assert raised.value.code == 2
        assert "cannot be combined with a rerun flag" in errors.getvalue()


def test_no_chapters_reaches_the_options_and_survives_every_preset() -> None:
    """
    The flag is an explicit choice, so it has to outlive the preset merge the way
    `--web-search` does. Both are applied after the merges for exactly that reason.
    """
    from deep_transcribe.cli_main import (
        _build_transcribe_options,  # pyright: ignore[reportPrivateUsage]
    )

    parser = build_parser()

    default = _build_transcribe_options(parser.parse_args(["URL"]))
    assert default.no_chapters is False
    assert default.web_search is False

    for arguments in (
        ["--no-chapters", "URL"],
        ["--deep", "--no-chapters", "URL"],
        ["--basic", "--with", "format", "--no-chapters", "URL"],
        ["--no_chapters", "URL"],
    ):
        options = _build_transcribe_options(parser.parse_args(arguments))
        assert options.no_chapters is True, arguments

    # And the two explicit choices do not cancel each other out.
    both = _build_transcribe_options(parser.parse_args(["--web-search", "--no-chapters", "URL"]))
    assert both.web_search is True
    assert both.no_chapters is True

    only_search = _build_transcribe_options(parser.parse_args(["--web-search", "URL"]))
    assert only_search.web_search is True
    assert only_search.no_chapters is False
