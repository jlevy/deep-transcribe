"""
Take a video or audio URL or local file, cache it, and produce a transcript source and
browser-ready HTML. Run `deep-transcribe --docs` for the complete operational guide,
or `deep-transcribe --help` for every processing choice and model profile action.

More information: https://github.com/jlevy/deep-transcribe
"""

import argparse
import json
import logging
import os
import sys
from collections.abc import Sequence
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Protocol

from deep_transcribe.model_profiles import (
    MODEL_PROFILES,
    ModelProvider,
    get_model_profile,
    set_model_profile,
)
from deep_transcribe.transcribe_options import TranscribeOptions

if TYPE_CHECKING:
    from deep_transcribe.transcription_metadata import TranscriptionMetadata

log = logging.getLogger(__name__)

APP_NAME = "deep-transcribe"

DESCRIPTION = "High-quality transcription, formatting, and analysis of videos and podcasts"

DEFAULT_WS = "./transcriptions"

MODELS_LIST = object()

# Conventional shell status for a process interrupted by SIGINT.
INTERRUPTED_EXIT_CODE = 130


def configure_kash_workspace(workspace: str | Path) -> Path:
    """Resolve the CLI workspace before importing Kash so its state stays local."""
    workspace_path = Path(workspace).expanduser().resolve()
    os.environ["KASH_WS_ROOT"] = str(workspace_path)
    return workspace_path


class _ArgumentContainer(Protocol):
    def add_argument(self, *args: str, **kwargs: Any) -> argparse.Action: ...


def get_app_version() -> str:
    try:
        return "v" + version(APP_NAME)
    except PackageNotFoundError:
        return "unknown"


def format_preset_help(preset_name: str, options: TranscribeOptions) -> str:
    """Generate concise help text for a processing preset."""
    enabled = options.get_enabled_options()
    if not enabled:
        return f"Transcribe only; no LLM formatting or annotations ({preset_name})"

    return f"Enable {', '.join(enabled)} ({preset_name})"


def get_all_available_options() -> str:
    """Get all processing stage names from `TranscribeOptions`."""
    from dataclasses import fields

    return ", ".join(field.name for field in fields(TranscribeOptions))


def _formatter_class() -> type[argparse.HelpFormatter]:
    return argparse.RawDescriptionHelpFormatter


def _add_version_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {get_app_version()}")


def _add_agent_arguments(parser: argparse.ArgumentParser) -> None:
    output = parser.add_argument_group("Built-in Documentation and Agent Skill")
    action = output.add_mutually_exclusive_group()
    action.add_argument(
        "--docs",
        action="store_true",
        help="Print the complete packaged Deep Transcribe guide",
    )
    action.add_argument(
        "--skill",
        action="store_true",
        help="Print the version-pinned Deep Transcribe SKILL.md",
    )
    action.add_argument(
        "--install-skill",
        action="store_true",
        help=(
            "Install the skill project-locally to portable, Claude, and AGENTS.md "
            "surfaces by default"
        ),
    )
    output.add_argument(
        "--surfaces",
        metavar="LIST",
        help=("With --install-skill: comma-separated portable, claude, agents-md, or all"),
    )
    output.add_argument(
        "--agent-base",
        type=Path,
        metavar="DIR",
        help="With --install-skill: write one explicit DIR/skills/deep-transcribe bundle",
    )


def _add_workspace_argument(parser: _ArgumentContainer) -> None:
    parser.add_argument(
        "--workspace",
        type=str,
        default=DEFAULT_WS,
        help="Workspace for outputs, metadata, model settings, and caches (default: %(default)s)",
    )


def _processing_stage_help() -> str:
    return dedent("""
        **Transcription backend:** Deepgram `nova-3` with `diarize_model=latest`.
        Supported language codes:
        https://developers.deepgram.com/docs/models-languages-overview#nova-3

        Processing stages accepted by `--with`:

        - `identify_speakers`: Name speakers using the fast LLM role.
        - `format`: Create paragraphs and backfill timestamps.
        - `insert_section_headings`: Add topic-based section headings.
        - `research_paras`: Add researched paragraph annotations.
        - `add_summary_bullets`: Add a concise, section-aligned outline.
        - `add_description`: Add a brief two-paragraph synopsis.
        - `insert_frame_captures`: Add representative frames for video sources.
        """).strip()


def _add_transcription_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    source = parser.add_argument_group("Source")
    source.add_argument(
        "source",
        type=str,
        nargs="?",
        metavar="SOURCE",
        help="YouTube or other media URL, or a local audio or video file",
    )

    presets = parser.add_argument_group("Processing Presets")
    presets.add_argument(
        "--basic",
        action="store_true",
        help=format_preset_help("basic", TranscribeOptions.basic()),
    )
    presets.add_argument(
        "--formatted",
        action="store_true",
        help=format_preset_help("formatted", TranscribeOptions.formatted()),
    )
    presets.add_argument(
        "--annotated",
        action="store_true",
        help=format_preset_help("annotated", TranscribeOptions.annotated()) + " (default)",
    )
    presets.add_argument(
        "--deep",
        action="store_true",
        help=format_preset_help("deep", TranscribeOptions.deep()),
    )

    processing = parser.add_argument_group("Custom Processing")
    processing.add_argument(
        "--with",
        dest="with_flags",
        type=str,
        metavar="STAGES",
        help=(
            "Comma-separated processing stages to add to the selected preset. "
            f"Choices: {get_all_available_options()}"
        ),
    )
    processing.add_argument(
        "--concepts",
        action="store_true",
        help=(
            "Extract a concept map: key concepts with glosses, timeline spans, and "
            "relations, shown in the transcript's analytics views (included in --deep)"
        ),
    )
    processing.add_argument(
        "--web-search",
        "--web_search",
        dest="web_search",
        action="store_true",
        help=(
            "Let the speaker roster step corroborate facts with web search "
            "(off by default; source metadata and your own context are used either way)"
        ),
    )
    processing.add_argument(
        "--elements",
        type=str,
        metavar="PARTS",
        help=(
            "Comma-separated page parts to include in the HTML export "
            "(default: everything). Choices: title, thumbnail, summary, timeline, "
            "speakers, outline, concepts, claims, frames, transcript"
        ),
    )
    processing.add_argument(
        "--no-minify",
        "--no_minify",
        dest="no_minify",
        action="store_true",
        help="Skip HTML, CSS, JavaScript, and Tailwind minification",
    )

    guidance = parser.add_argument_group("Natural-Language Guidance")
    guidance.add_argument(
        "--context",
        action="append",
        default=[],
        metavar="TEXT",
        help=(
            "Describe participants, roles, chronology, terminology, and source facts in "
            "ordinary prose; repeat to join paragraphs"
        ),
    )
    guidance.add_argument(
        "--context-file",
        action="append",
        default=[],
        type=Path,
        metavar="PATH",
        help="UTF-8 prose to use as recording context; repeat to join files",
    )
    guidance.add_argument(
        "--segments",
        metavar="PATH",
        help=(
            "YAML listing stretches to mark (teaser, intro, promo, outro); suppressed "
            "ones are left out of the analysis. Editing it and rerunning reuses the "
            "transcript. Hints stick to the source; pass `none` to clear them"
        ),
    )
    guidance.add_argument(
        "--instructions",
        action="append",
        default=[],
        metavar="TEXT",
        help=(
            "Trusted post-transcription processing instructions; repeat to join "
            "paragraphs. Instructions stick to the source; pass `none` to clear them"
        ),
    )
    guidance.add_argument(
        "--instructions-file",
        action="append",
        default=[],
        type=Path,
        metavar="PATH",
        help="UTF-8 post-transcription processing instructions; repeat to join files",
    )

    overrides = parser.add_argument_group("Exact and Structured Overrides")
    overrides.add_argument(
        "--title",
        metavar="TEXT",
        help="Exact title for the transcript and exported HTML",
    )
    overrides.add_argument(
        "--description",
        metavar="TEXT",
        help="Concise source description to include with the recording context",
    )
    overrides.add_argument(
        "--metadata",
        type=Path,
        metavar="YAML_OR_JSON",
        help=(
            "Optional structured overrides for automation: title, description, "
            "additional_context, processing_instructions, key_terms, speaker_hints, "
            "speaker_roster, or extra fields"
        ),
    )
    overrides.add_argument(
        "--key-term",
        action="append",
        default=[],
        metavar="TERM",
        help="Term or name Deepgram should recognize accurately; repeat as needed",
    )
    overrides.add_argument(
        "--speaker",
        action="append",
        default=[],
        type=_speaker_hint,
        metavar="ID=NAME",
        help="Authoritative speaker label, such as 0='Alice Chen'; repeat as needed",
    )
    overrides.add_argument(
        "--speaker-role",
        action="append",
        default=[],
        metavar="NAME_OR_ROLE",
        help=(
            "Exact speaker name or role for boundary correction; repeat for a complete "
            "roster only when prose inference needs an override"
        ),
    )
    execution = parser.add_argument_group("Models, Execution, and Output")
    _add_workspace_argument(execution)
    execution.add_argument(
        "--models",
        nargs="?",
        const=MODELS_LIST,
        type=ModelProvider,
        metavar="PROFILE",
        help=(
            "List model profiles with no value, or persist anthropic/openai before an "
            "optional transcription"
        ),
    )
    execution.add_argument(
        "--language",
        type=str,
        default="en",
        help="Deepgram Nova-3 language code; use 'multi' for multilingual audio",
    )
    execution.add_argument(
        "--transcription-model",
        default="nova-3",
        help="Deepgram speech-to-text model (default: %(default)s)",
    )
    execution.add_argument(
        "--diarize-model",
        default="latest",
        help="Deepgram speaker diarization model (default: %(default)s)",
    )
    execution.add_argument(
        "--rerun",
        action="store_true",
        help="Force every stage to rerun, including paid speech-to-text transcription",
    )
    execution.add_argument(
        "--rerun-processing",
        action="store_true",
        help=(
            "Force every post-transcription stage to rerun while reusing the raw transcript cache"
        ),
    )
    execution.add_argument(
        "--json",
        action="store_true",
        help="Print final workspace and artifact paths as JSON",
    )


def _help_epilog() -> str:
    return (
        _processing_stage_help()
        + "\n\n"
        + dedent("""
        **Model provider:** New workspaces use the Anthropic profile. Run
        `deep-transcribe --models` to inspect both profiles or
        `deep-transcribe --models openai` to persist the OpenAI profile in this
        workspace. Add a source to select the profile and transcribe in one invocation.

        **Context:** Start with `--context` or `--context-file` in ordinary prose. The
        speaker-identification LLM uses those facts to produce its structured mapping.
        Supported media URLs also contribute bounded extractor metadata automatically;
        use context for relevant facts the source does not publish. When the prose clearly
        names the complete set of speaking roles, Deep Transcribe also derives the roster
        needed to repair merged diarization boundaries. Exact speaker IDs, repeated
        `--speaker-role` values, and YAML/JSON metadata are optional overrides, not the
        normal human interface.

        **Iterative reruns:** A normal rerun resumes at the first affected stage and
        reuses compatible cached work. Updating descriptive context or speaker metadata
        preserves speech-to-text. Updating processing instructions resumes at the
        overview stages. Changing key terms, the language, or a Deepgram model creates a
        new transcription cache entry. `--rerun-processing` forces every post-transcription
        stage while preserving the raw transcript. `--rerun` forces every stage,
        including speech-to-text.

        Examples:

        ```shell
        deep-transcribe --basic ./interview.mp3
        deep-transcribe --annotated https://youtu.be/VIDEO_ID
        deep-transcribe --deep --language multi URL
        deep-transcribe --basic --with format URL
        deep-transcribe --context "Alice hosts; Bob presents." URL
        deep-transcribe --context-file recording.txt URL
        deep-transcribe --speaker 0="Alice Chen" --key-term SignalFlow URL
        deep-transcribe --instructions "Keep the outline concise." URL
        deep-transcribe --models
        deep-transcribe --models openai URL
        ```
        """).strip()
    )


def _profile_help() -> str:
    lines: list[str] = []
    for provider, profile in MODEL_PROFILES.items():
        suffix = " (default)" if provider is ModelProvider.anthropic else ""
        lines.extend(
            [
                f"{provider.value}{suffix}",
                f"  careful:    {profile.careful_llm}",
                f"  structured: {profile.structured_llm}",
                f"  standard:   {profile.standard_llm}",
                f"  fast:       {profile.fast_llm}",
            ]
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """Build the canonical, self-documenting command parser."""
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        formatter_class=_formatter_class(),
        description=DESCRIPTION,
        epilog=_help_epilog() + f"\n\n{APP_NAME} {get_app_version()}",
    )
    _add_version_argument(parser)
    _add_transcription_arguments(parser)
    _add_agent_arguments(parser)
    return parser


def _parse_args(argv: Sequence[str]) -> tuple[argparse.ArgumentParser, argparse.Namespace]:
    parser = build_parser()
    return parser, parser.parse_args(argv)


def display_results(
    base_dir: Path,
    transcript_path: Path,
    html_path: Path,
    *,
    as_json: bool,
) -> None:
    """Display generated artifact paths."""
    from deep_transcribe.transcribe_commands import SUGGESTED_SEGMENTS_NAME

    # `base_dir` is the root the user passed; the kash workspace, where the pipeline
    # writes, is a level inside it. The transcript is always in that workspace's docs
    # directory, so it is the reliable way back to it.
    suggested = transcript_path.parent.parent / SUGGESTED_SEGMENTS_NAME
    if as_json:
        result: dict[str, str] = {
            "workspace": str(base_dir.resolve()),
            "transcript": str(transcript_path.resolve()),
            "html": str(html_path.resolve()),
        }
        # An agent driving the review loop needs to find this without reading the log.
        if suggested.exists():
            result["suggested_segments"] = str(suggested.resolve())
        print(json.dumps(result, sort_keys=True))
        return

    # fmt_path is missing from prettyfmt's __all__ (upstream oversight); it is public API.
    from prettyfmt import fmt_path  # pyright: ignore[reportPrivateImportUsage]
    from rich import print as rprint

    rprint(
        dedent(f"""
            [green]All done![/green]

            All results are stored in the workspace:

                [yellow]{fmt_path(base_dir)}[/yellow]

            The transcript source is at:

                [yellow]{fmt_path(transcript_path)}[/yellow]

            Browser-ready HTML is at:

                [yellow]{fmt_path(html_path)}[/yellow]

            To inspect other cached or intermediate outputs, run `kash`, change to the
            workspace, and use `files`, `show`, `help`, and related commands.
            """)
    )
    if suggested.exists():
        rprint(
            dedent(f"""
                The opening of this recording repeats later, which usually means a
                highlight reel. Suggested segment hints are at:

                    [yellow]{fmt_path(suggested)}[/yellow]

                Review them and rerun with `--segments` to leave that stretch out of the
                analysis. The transcript is reused, so the rerun is quick.
                """)
        )


def _display_model_profiles(
    *,
    as_json: bool,
    active: ModelProvider | None,
    workspace_path: Path,
    selected: ModelProvider | None = None,
) -> None:
    profile_data = {
        provider.value: profile.as_params() for provider, profile in MODEL_PROFILES.items()
    }
    if as_json:
        output: dict[str, object] = {
            "active": active.value if active is not None else "custom",
            "default": ModelProvider.anthropic.value,
            "profiles": profile_data,
            "workspace": str(workspace_path),
        }
        if selected:
            output["selected"] = selected.value
        print(json.dumps(output, sort_keys=True))
        return

    print("Model profiles:\n")
    print(_profile_help())
    print(f"\nActive in {workspace_path}: {active.value if active else 'custom'}.")
    if selected:
        print(f"\nSaved the {selected.value} profile in {workspace_path}.")
    else:
        print("\nUse `deep-transcribe --models PROFILE` to save a profile.")


def _speaker_hint(value: str) -> tuple[str, str]:
    speaker_id, separator, name = value.partition("=")
    if not separator or not speaker_id.strip() or not name.strip():
        raise argparse.ArgumentTypeError("speaker hints must use ID=NAME")
    return speaker_id.strip(), name.strip()


CLEAR_TOKEN = "none"
"""
Literal value that clears a sticky guidance input instead of setting one.

`--segments` and `--instructions` are written back onto the stored source, so a later run
without the flag still honors them. Without a spelling for "remove it" the only way back
is hand-editing the resource YAML in the workspace.
"""


def _is_clear_token(value: object) -> bool:
    """Whether a flag value is the literal clear request rather than a value to store."""
    return str(value).strip().casefold() == CLEAR_TOKEN


def build_transcription_metadata(args: argparse.Namespace) -> "TranscriptionMetadata":
    from deep_transcribe.transcription_metadata import (
        TranscriptionMetadata,
        load_transcription_metadata,
        transcription_metadata_from_mapping,
    )

    metadata = (
        load_transcription_metadata(args.metadata) if args.metadata else TranscriptionMetadata()
    )
    context_parts = [path.read_text(encoding="utf-8").strip() for path in args.context_file] + [
        value.strip() for value in args.context
    ]
    context_parts = [value for value in context_parts if value]

    inline_data: dict[str, object] = {}
    if args.title:
        inline_data["title"] = args.title
    if args.description:
        inline_data["description"] = args.description
    if context_parts:
        inline_data["additional_context"] = "\n\n".join(context_parts)
    if args.key_term:
        inline_data["key_terms"] = list(dict.fromkeys([*metadata.key_terms, *args.key_term]))
    if args.speaker:
        inline_data["speaker_hints"] = dict(args.speaker)
    if args.speaker_role:
        inline_data["speaker_roster"] = list(
            dict.fromkeys([*metadata.speaker_roster, *args.speaker_role])
        )
    segments_arg = getattr(args, "segments", None)
    clear_segments = bool(segments_arg) and _is_clear_token(segments_arg)
    if segments_arg and not clear_segments:
        from deep_transcribe.segment_hints import format_time, load_hints

        hints = load_hints(Path(segments_arg))
        if hints.segments:
            overlaps = hints.overlaps()
            if overlaps:
                log.warning(
                    "%d segment hint pair(s) overlap; the earlier one wins where they do",
                    len(overlaps),
                )
            inline_data["segments"] = {
                "segments": [
                    {
                        "at": f"{format_time(h.start)} - {format_time(h.end)}",
                        "purpose": h.purpose.value,
                        **({"suppress": h.suppress} if h.suppress is not None else {}),
                        **({"note": h.note} if h.note else {}),
                    }
                    for h in hints.segments
                ]
            }

    instruction_values = [value.strip() for value in args.instructions]
    clear_instructions = any(_is_clear_token(value) for value in instruction_values)
    instruction_parts = (
        [metadata.processing_instructions or ""]
        + [path.read_text(encoding="utf-8").strip() for path in args.instructions_file]
        + [value for value in instruction_values if not _is_clear_token(value)]
    )
    instruction_parts = [value for value in instruction_parts if value]
    if instruction_parts:
        inline_data["processing_instructions"] = "\n\n".join(instruction_parts)

    if inline_data:
        metadata = metadata.merged_with(transcription_metadata_from_mapping(inline_data))
    # Supplying replacement text already overwrites the stored value, so `none` alongside
    # real instructions is the text winning rather than a clear.
    clear_instructions = clear_instructions and not instruction_parts
    if clear_segments or clear_instructions:
        from dataclasses import replace

        metadata = replace(
            metadata,
            clear_segments=metadata.clear_segments or clear_segments,
            clear_processing_instructions=(
                metadata.clear_processing_instructions or clear_instructions
            ),
        )
    return metadata


def _build_transcribe_options(args: argparse.Namespace) -> TranscribeOptions:
    if not any([args.basic, args.formatted, args.annotated, args.deep]):
        options = TranscribeOptions.annotated()
    else:
        options = TranscribeOptions.basic()

    if args.basic:
        options = options.merge_with(TranscribeOptions.basic())
    if args.formatted:
        options = options.merge_with(TranscribeOptions.formatted())
    if args.annotated:
        options = options.merge_with(TranscribeOptions.annotated())
    if args.deep:
        options = options.merge_with(TranscribeOptions.deep())
    if args.with_flags:
        options = options.merge_with(TranscribeOptions.from_with_flags(args.with_flags))

    if args.concepts:
        options = options.merge_with(TranscribeOptions(extract_concepts=True))

    # Presets do not carry this: it is an explicit opt-in that must outlive them.
    if args.web_search:
        from dataclasses import replace

        options = replace(options, web_search=True)

    return options


def _parse_skill_surfaces(
    value: str | None,
    parser: argparse.ArgumentParser,
) -> frozenset[str] | None:
    if value is None:
        return None

    from deep_transcribe.skill_support import ALL_SURFACES

    tokens = [token.strip() for token in value.split(",") if token.strip()]
    if not tokens:
        parser.error(
            "--surfaces requires a comma-separated list of portable, claude, agents-md, or all"
        )

    selected: set[str] = set()
    for token in tokens:
        if token == "all":
            selected.update(ALL_SURFACES)
        elif token in ALL_SURFACES:
            selected.add(token)
        else:
            parser.error(
                f"unknown skill surface {token!r}; choose portable, claude, agents-md, or all"
            )
    return frozenset(selected)


def _handle_documentation_and_skill_options(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> bool:
    docs = bool(getattr(args, "docs", False))
    skill = bool(getattr(args, "skill", False))
    install = bool(getattr(args, "install_skill", False))
    surfaces_value = getattr(args, "surfaces", None)
    agent_base = getattr(args, "agent_base", None)
    action_requested = docs or skill or install

    if not install and (surfaces_value is not None or agent_base is not None):
        parser.error("--surfaces and --agent-base require --install-skill")
    if action_requested and args.models is not None:
        parser.error("--models cannot be combined with documentation or skill actions")
    if action_requested and args.source is not None:
        parser.error("a source cannot be combined with documentation or skill actions")

    if docs:
        from deep_transcribe.skill_support import get_docs_content

        print(get_docs_content(), end="")
        return True

    if skill:
        from deep_transcribe.skill_support import compose_skill

        print(compose_skill(), end="")
        return True

    if install:
        from deep_transcribe.skill_support import install_skill

        if agent_base is not None and surfaces_value is not None:
            parser.error("--surfaces cannot be combined with --agent-base")
        selected = _parse_skill_surfaces(surfaces_value, parser)
        results = install_skill(agent_base=agent_base, surfaces=selected)
        if any(result.action == "blocked-newer" for result in results):
            raise SystemExit(1)
        return True

    return False


def _run_cli(argv: Sequence[str] | None = None) -> None:
    cli_argv = list(argv) if argv is not None else sys.argv[1:]
    parser, args = _parse_args(cli_argv)

    if not cli_argv:
        parser.print_help()
        return

    if _handle_documentation_and_skill_options(parser, args):
        return

    try:
        if args.models is MODELS_LIST:
            if args.source is not None:
                parser.error("--models without a profile cannot be combined with a source")
            active, workspace_path = get_model_profile(Path(args.workspace))
            _display_model_profiles(
                as_json=args.json,
                active=active,
                workspace_path=workspace_path,
            )
            return

        if isinstance(args.models, ModelProvider):
            workspace_path = set_model_profile(Path(args.workspace), args.models)
            if args.source is None:
                _display_model_profiles(
                    as_json=args.json,
                    active=args.models,
                    selected=args.models,
                    workspace_path=workspace_path,
                )
                return
    except ValueError as error:
        parser.error(str(error))

    if args.source is None:
        parser.error("a source is required unless an action such as --models or --docs is used")

    workspace = configure_kash_workspace(args.workspace)

    from kash.config.settings import LogLevel
    from kash.config.setup import kash_setup

    kash_setup(
        kash_ws_root=workspace,
        rich_logging=True,
        console_log_level=LogLevel.warning,
    )

    # Fail fast, after kash setup has loaded .env files, if required keys are absent.
    from deep_transcribe.api_keys import format_missing_keys_message, missing_api_keys

    options = _build_transcribe_options(args)
    missing_keys = missing_api_keys(options, workspace)
    if missing_keys:
        if args.json:
            print(
                json.dumps(
                    {
                        "error": "missing API keys",
                        "missing": [key.var for key in missing_keys],
                        "help": "deep-transcribe --docs",
                    },
                    sort_keys=True,
                ),
                file=sys.stderr,
            )
        else:
            from rich import print as rprint

            rprint(f"[red]{format_missing_keys_message(missing_keys)}[/red]")
        raise SystemExit(2)

    try:
        from deep_transcribe.transcribe_commands import run_transcription

        elements = None
        if args.elements:
            from deep_transcribe.transcribe_commands import parse_page_elements

            try:
                elements = parse_page_elements(args.elements)
            except ValueError as error:
                parser.error(str(error))

        # A hints or metadata file the user wrote is an argument, so a mistake in one is a
        # usage error: reported as one line, before the generic handler below turns it into
        # a traceback pointing at our own parser.
        try:
            metadata = build_transcription_metadata(args)
        except ValueError as error:
            parser.error(str(error))

        transcript_path, html_path = run_transcription(
            workspace,
            args.source,
            options,
            args.language,
            transcription_model=args.transcription_model,
            diarize_model=args.diarize_model,
            metadata=metadata,
            no_minify=args.no_minify,
            rerun=args.rerun,
            rerun_processing=args.rerun_processing,
            elements=elements,
        )
        display_results(
            workspace,
            transcript_path,
            html_path,
            as_json=args.json,
        )
    except Exception as error:
        from kash.config.logger import get_log_settings

        from deep_transcribe.media_errors import explain_error

        # A recognized failure already knows the whole story, and a traceback through
        # yt-dlp's internals tells the user nothing they can act on. Log it at info so the
        # detail still reaches the log file — whose path is printed either way — while the
        # console gets the one line. Anything unrecognized keeps the full report, because a
        # confident wrong summary is worse than a stack trace.
        explained = explain_error(error, source=args.source, workspace_path=workspace)
        if explained is None:
            log.error("Error running deep transcription", exc_info=error)
        else:
            log.info("Error running deep transcription", exc_info=error)
        log_file = get_log_settings().log_file_path
        if args.json:
            print(
                json.dumps(
                    {"error": explained or str(error), "log": str(log_file)}, sort_keys=True
                ),
                file=sys.stderr,
            )
        else:
            # fmt_path is missing from prettyfmt's __all__ (upstream oversight); it is public API.
            from prettyfmt import fmt_path  # pyright: ignore[reportPrivateImportUsage]
            from rich import print as rprint

            rprint(f"[red]{explained or f'Error: {error}'}[/red]")
            rprint(f"[bright_black]See logs for more details: {fmt_path(log_file)}[/bright_black]")
        raise SystemExit(1) from error


def main(argv: Sequence[str] | None = None) -> int | None:
    try:
        _run_cli(argv)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return INTERRUPTED_EXIT_CODE
    return None


if __name__ == "__main__":
    raise SystemExit(main())
