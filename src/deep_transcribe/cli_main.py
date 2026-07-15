"""
Take a video or audio URL or local file, cache it, and produce a transcript source and
browser-ready HTML. Run `deep-transcribe transcribe --help` for processing choices,
`deep-transcribe models --help` for Anthropic and OpenAI profiles, and
`deep-transcribe mcp --help` for agent integrations.

More information: https://github.com/jlevy/deep-transcribe
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Sequence
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from textwrap import dedent
from typing import Any, Protocol

from deep_transcribe.model_profiles import MODEL_PROFILES, ModelProvider, set_model_profile
from deep_transcribe.transcribe_options import TranscribeOptions

log = logging.getLogger(__name__)

APP_NAME = "deep-transcribe"

DESCRIPTION = "High-quality transcription, formatting, and analysis of videos and podcasts"

DEFAULT_WS = "./transcriptions"

DEFAULT_MCP_SERVER_PORT = 4440

COMMANDS = {"transcribe", "models", "mcp", "logs"}


class _ArgumentContainer(Protocol):
    def add_argument(self, *args: str, **kwargs: Any) -> argparse.Action: ...


class _SubparserCollection(Protocol):
    def add_parser(self, name: str, **kwargs: Any) -> argparse.ArgumentParser: ...


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
        - `add_summary_bullets`: Add a concise summary.
        - `add_description`: Add a document description.
        - `insert_frame_captures`: Add representative frames for video sources.
        """).strip()


def _add_transcription_arguments(
    parser: argparse.ArgumentParser,
    *,
    source_required: bool,
) -> None:
    parser.add_argument(
        "source",
        type=str,
        nargs=None if source_required else "?",
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
        "--no-minify",
        "--no_minify",
        dest="no_minify",
        action="store_true",
        help="Skip HTML, CSS, JavaScript, and Tailwind minification",
    )

    execution = parser.add_argument_group("Execution and Output")
    _add_workspace_argument(execution)
    execution.add_argument(
        "--language",
        type=str,
        default="en",
        help="Deepgram Nova-3 language code; use 'multi' for multilingual audio",
    )
    execution.add_argument(
        "--rerun",
        action="store_true",
        help="Rerun processing stages even when cached outputs exist",
    )
    execution.add_argument(
        "--json",
        action="store_true",
        help="Print final workspace and artifact paths as JSON",
    )


def _build_transcribe_parser(subparsers: _SubparserCollection) -> None:
    epilog = (
        _processing_stage_help()
        + "\n\n"
        + dedent("""
        **Model provider:** New workspaces use the Anthropic profile. Run
        `deep-transcribe models` to inspect both profiles or
        `deep-transcribe models --set openai` to persist the OpenAI profile in
        this workspace.

        Examples:

        ```shell
        deep-transcribe transcribe --basic ./interview.mp3
        deep-transcribe transcribe --annotated https://youtu.be/VIDEO_ID
        deep-transcribe transcribe --deep --language multi URL
        deep-transcribe transcribe --basic --with format URL
        ```
        """).strip()
    )
    parser = subparsers.add_parser(
        "transcribe",
        help="Transcribe and process a URL or local media file",
        description="Transcribe and process a URL or local media file.",
        formatter_class=_formatter_class(),
        epilog=epilog,
    )
    parser.set_defaults(command="transcribe")
    _add_transcription_arguments(parser, source_required=True)


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


def _profile_markdown() -> str:
    lines: list[str] = []
    for provider, profile in MODEL_PROFILES.items():
        suffix = " (default)" if provider is ModelProvider.anthropic else ""
        lines.append(
            f"- **`{provider.value}`{suffix}:** careful `{profile.careful_llm}`; "
            f"structured `{profile.structured_llm}`; standard `{profile.standard_llm}`; "
            f"fast `{profile.fast_llm}`."
        )
    return "\n".join(lines)


def _build_models_parser(subparsers: _SubparserCollection) -> None:
    epilog = (
        "Current profiles:\n\n"
        + _profile_markdown()
        + "\n\n"
        + dedent("""
        Examples:

        ```shell
        deep-transcribe models
        deep-transcribe models --json
        deep-transcribe models --set openai
        deep-transcribe models --workspace ./other-output --set anthropic
        ```
        """).strip()
    )
    parser = subparsers.add_parser(
        "models",
        help="Inspect or select Anthropic and OpenAI model profiles",
        description="Inspect or persist the LLM role profile used by transcription processing.",
        formatter_class=_formatter_class(),
        epilog=epilog,
    )
    parser.set_defaults(command="models")
    parser.add_argument(
        "--set",
        dest="provider",
        choices=tuple(ModelProvider),
        type=ModelProvider,
        help="Persist a provider profile in the selected workspace",
    )
    _add_workspace_argument(parser)
    parser.add_argument("--json", action="store_true", help="Print profile data as JSON")


def _build_mcp_parser(subparsers: _SubparserCollection) -> None:
    parser = subparsers.add_parser(
        "mcp",
        help="Expose all four transcription presets as MCP tools",
        description="Run an MCP server exposing basic, formatted, annotated, and deep tools.",
        formatter_class=_formatter_class(),
        epilog=dedent(f"""
            Tools:

            - `transcribe_basic`
            - `transcribe_formatted`
            - `transcribe_annotated`
            - `transcribe_deep`

            Examples:

            ```shell
            deep-transcribe mcp
            deep-transcribe mcp --transport sse
            ```

            SSE listens on http://127.0.0.1:{DEFAULT_MCP_SERVER_PORT}.
            """),
    )
    parser.set_defaults(command="mcp")
    parser.add_argument(
        "--transport",
        choices=("stdio", "sse"),
        default="stdio",
        help="MCP transport (default: %(default)s)",
    )
    _add_workspace_argument(parser)


def _build_logs_parser(subparsers: _SubparserCollection) -> None:
    parser = subparsers.add_parser(
        "logs",
        help="Follow MCP server logs",
        description="Follow all Deep Transcribe MCP server logs.",
        formatter_class=_formatter_class(),
    )
    parser.set_defaults(command="logs")
    _add_workspace_argument(parser)


def build_parser() -> argparse.ArgumentParser:
    """Build the canonical, self-documenting command parser."""
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        formatter_class=_formatter_class(),
        description=DESCRIPTION,
        epilog=dedent(f"""
            **Getting started:** `{APP_NAME} transcribe --help`

            **IMPORTANT:** Run `{APP_NAME} <command> --help` before using a command.
            Legacy flag-only invocations remain supported for backward compatibility.

            {APP_NAME} {get_app_version()}
            """),
    )
    _add_version_argument(parser)
    subparsers = parser.add_subparsers(dest="command", title="Commands", metavar="COMMAND")
    _build_transcribe_parser(subparsers)
    _build_models_parser(subparsers)
    _build_mcp_parser(subparsers)
    _build_logs_parser(subparsers)
    return parser


def build_legacy_parser() -> argparse.ArgumentParser:
    """Build the pre-command parser retained for backward compatibility."""
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        formatter_class=_formatter_class(),
        description=DESCRIPTION,
        epilog=dedent(f"""
            This flag-only form remains supported. New scripts and agents should use:

            - `{APP_NAME} transcribe --help`
            - `{APP_NAME} models --help`
            - `{APP_NAME} mcp --help`

            {APP_NAME} {get_app_version()}
            """),
    )
    parser.set_defaults(command="legacy")
    _add_version_argument(parser)
    _add_transcription_arguments(parser, source_required=False)

    server = parser.add_argument_group("MCP Compatibility Flags")
    server.add_argument("--mcp", action="store_true", help="Run the stdio MCP server")
    server.add_argument(
        "--sse",
        action="store_true",
        help=f"Run the SSE MCP server on http://127.0.0.1:{DEFAULT_MCP_SERVER_PORT}",
    )
    server.add_argument("--logs", action="store_true", help="Follow MCP server logs")
    return parser


def _parse_args(argv: Sequence[str]) -> tuple[argparse.ArgumentParser, argparse.Namespace]:
    if not argv or argv[0] in COMMANDS or argv[0] in {"-h", "--help", "--version"}:
        parser = build_parser()
    else:
        parser = build_legacy_parser()
    return parser, parser.parse_args(argv)


def display_results(
    base_dir: Path,
    transcript_path: Path,
    html_path: Path,
    *,
    as_json: bool,
) -> None:
    """Display generated artifact paths."""
    if as_json:
        print(
            json.dumps(
                {
                    "workspace": str(base_dir.resolve()),
                    "transcript": str(transcript_path.resolve()),
                    "html": str(html_path.resolve()),
                },
                sort_keys=True,
            )
        )
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


def _display_model_profiles(
    *,
    as_json: bool,
    selected: ModelProvider | None = None,
    workspace_path: Path | None = None,
) -> None:
    profile_data = {
        provider.value: profile.as_params() for provider, profile in MODEL_PROFILES.items()
    }
    if as_json:
        output: dict[str, object] = {
            "default": ModelProvider.anthropic.value,
            "profiles": profile_data,
        }
        if selected:
            output["selected"] = selected.value
        if workspace_path:
            output["workspace"] = str(workspace_path)
        print(json.dumps(output, sort_keys=True))
        return

    print("Model profiles:\n")
    print(_profile_help())
    if selected:
        print(f"\nSaved the {selected.value} profile in {workspace_path}.")
    else:
        print("\nUse `deep-transcribe models --set PROVIDER` to save a profile.")


def _run_mcp_server(*, transport: str) -> None:
    from kash.mcp.mcp_main import McpMode, run_mcp_server

    mcp_mode = McpMode.standalone_sse if transport == "sse" else McpMode.standalone_stdio
    action_names = [
        "transcribe_annotated",
        "transcribe_formatted",
        "transcribe_basic",
        "transcribe_deep",
    ]
    run_mcp_server(mcp_mode, proxy_to=None, tool_names=action_names)


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

    return options


def main(argv: Sequence[str] | None = None) -> None:
    cli_argv = list(argv) if argv is not None else sys.argv[1:]
    parser, args = _parse_args(cli_argv)

    if not cli_argv:
        parser.print_help()
        return

    if args.command == "models":
        workspace_path = None
        if args.provider:
            workspace_path = set_model_profile(Path(args.workspace), args.provider)
        _display_model_profiles(
            as_json=args.json,
            selected=args.provider,
            workspace_path=workspace_path,
        )
        return

    from kash.config.settings import LogLevel
    from kash.config.setup import kash_setup

    workspace = Path(args.workspace).expanduser().resolve()
    kash_setup(
        kash_ws_root=workspace,
        rich_logging=True,
        console_log_level=LogLevel.warning,
    )

    if args.command == "mcp":
        _run_mcp_server(transport=args.transport)
        return

    if args.command == "logs":
        from kash.mcp.mcp_server_commands import mcp_logs

        mcp_logs(follow=True, all=True)
        return

    if args.command == "legacy":
        if args.logs:
            from kash.mcp.mcp_server_commands import mcp_logs

            mcp_logs(follow=True, all=True)
            return
        if args.mcp or args.sse:
            _run_mcp_server(transport="sse" if args.sse else "stdio")
            return
        if not args.source:
            parser.error("SOURCE is required unless an MCP compatibility flag is specified")

    try:
        from deep_transcribe.transcribe_commands import run_transcription

        transcript_path, html_path = run_transcription(
            workspace,
            args.source,
            _build_transcribe_options(args),
            args.language,
            no_minify=args.no_minify,
            rerun=args.rerun,
        )
        display_results(
            workspace,
            transcript_path,
            html_path,
            as_json=args.json,
        )
    except Exception as error:
        from kash.config.logger import get_log_settings

        log.error("Error running deep transcription", exc_info=error)
        log_file = get_log_settings().log_file_path
        if args.json:
            print(
                json.dumps({"error": str(error), "log": str(log_file)}, sort_keys=True),
                file=sys.stderr,
            )
        else:
            # fmt_path is missing from prettyfmt's __all__ (upstream oversight); it is public API.
            from prettyfmt import fmt_path  # pyright: ignore[reportPrivateImportUsage]
            from rich import print as rprint

            rprint(f"[red]Error: {error}[/red]")
            rprint(f"[bright_black]See logs for more details: {fmt_path(log_file)}[/bright_black]")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
