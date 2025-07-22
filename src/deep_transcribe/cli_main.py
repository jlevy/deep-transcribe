"""
Take a video or audio URL (such as YouTube), download and cache it, and perform a "deep
transcription" of it, including full transcription, identifying speakers, adding
sections, timestamps, and annotations, and inserting frame captures.

More information: https://github.com/jlevy/deep-transcribe
"""

from __future__ import annotations

import argparse
import logging
import sys
from importlib.metadata import version
from pathlib import Path
from textwrap import dedent

from clideps.utils.readable_argparse import ReadableColorFormatter
from kash.config.settings import DEFAULT_MCP_SERVER_PORT
from prettyfmt import fmt_path
from rich import print as rprint

from deep_transcribe.transcribe_commands import run_transcription
from deep_transcribe.transcribe_options import TranscribeOptions

log = logging.getLogger(__name__)

APP_NAME = "deep-transcribe"

DESCRIPTION = """High-quality transcription, formatting, and analysis of videos and podcasts"""

DEFAULT_WS = "./transcriptions"


def get_app_version() -> str:
    try:
        return "v" + version(APP_NAME)
    except Exception:
        return "unknown"


def format_preset_help(preset_name: str, options: TranscribeOptions) -> str:
    """Generate help text for a preset showing equivalent --with options."""
    enabled = options.get_enabled_options()
    if not enabled:
        return f"Transcribe with {preset_name!r} options"

    enabled_str = ",".join(enabled)
    return f"Transcribe with {preset_name!r} options, which is equivalent to the options: {enabled_str}"


def get_all_available_options() -> str:
    """Get all available option names from TranscribeOptions."""
    options = TranscribeOptions()
    all_options = list(options.__dataclass_fields__.keys())
    return ", ".join(all_options)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        formatter_class=ReadableColorFormatter,
        epilog=dedent((__doc__ or "") + "\n\n" + f"{APP_NAME} {get_app_version()}"),
        description=DESCRIPTION,
    )
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {get_app_version()}")

    # URL argument (required unless --mcp is used)
    parser.add_argument("url", type=str, nargs="?", help="URL of the video or audio to transcribe")

    # Preset flags (listed first for visibility)
    parser.add_argument(
        "--basic",
        action="store_true",
        help=format_preset_help("basic", TranscribeOptions.basic()),
    )
    parser.add_argument(
        "--formatted",
        action="store_true",
        help=format_preset_help("formatted", TranscribeOptions.formatted()),
    )
    parser.add_argument(
        "--annotated",
        action="store_true",
        help=format_preset_help("annotated", TranscribeOptions.annotated()) + " (default)",
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        help=format_preset_help("deep", TranscribeOptions.deep()),
    )

    # Option flags (right after presets)
    parser.add_argument(
        "--with",
        dest="with_flags",
        type=str,
        help=(
            f"Comma-separated list of processing options. Available options: "
            f"{get_all_available_options()}. Default preset is --annotated."
        ),
    )

    # Transcription options
    parser.add_argument(
        "--no_minify",
        action="store_true",
        help="Skip HTML/CSS/JS/Tailwind minification step",
    )

    # Common arguments
    parser.add_argument(
        "--workspace",
        type=str,
        default=DEFAULT_WS,
        help="the workspace directory to use for files, metadata, and cache",
    )
    parser.add_argument(
        "--language",
        type=str,
        default="en",
        help="language of the video or audio to transcribe",
    )
    parser.add_argument(
        "--rerun", action="store_true", help="rerun actions even if the outputs already exist"
    )

    # MCP mode
    parser.add_argument(
        "--mcp",
        action="store_true",
        help="Run as an MCP server instead of transcribing",
    )
    parser.add_argument(
        "--sse",
        action="store_true",
        help=f"Run as an SSE MCP server at: http://127.0.0.1:{DEFAULT_MCP_SERVER_PORT} (implies --mcp)",
    )
    parser.add_argument(
        "--logs",
        action="store_true",
        help="Just tail the logs from the MCP server in the terminal (implies --mcp)",
    )

    return parser


def display_results(base_dir: Path, md_path: Path, html_path: Path) -> None:
    """Display the results of transcription to the user."""
    rprint(
        dedent(f"""
            [green]All done![/green]

            All results are stored the workspace:

                [yellow]{fmt_path(base_dir)}[/yellow]

            Cleanly formatted Markdown (with a few HTML tags for citations) is at:

                [yellow]{fmt_path(md_path)}[/yellow]

            Browser-ready HTML is at:

                [yellow]{fmt_path(html_path)}[/yellow]

            If you like, you can run the kash shell with all deep transcription tools loaded,
            and use this to see other outputs or perform other tasks:
                [blue]deep_transcribe kash[/blue]
            Then cd into the workspace and use `files`, `show`, `help`, etc.
            """)
    )


def main() -> None:
    # Set up kash logging
    from kash.config.settings import LogLevel
    from kash.config.setup import kash_setup

    kash_setup(rich_logging=True, console_log_level=LogLevel.warning)

    parser = build_parser()
    args = parser.parse_args()

    # Auto-enable MCP mode if --sse or --logs is used
    if args.sse or args.logs:
        args.mcp = True

    # Run as an MCP server
    if args.mcp:
        from kash.mcp.mcp_main import McpMode, run_mcp_server
        from kash.mcp.mcp_server_commands import mcp_logs

        if args.logs:
            mcp_logs(follow=True, all=True)
        else:
            mcp_mode = McpMode.standalone_sse if args.sse else McpMode.standalone_stdio
            # For MCP, expose transcribe actions (annotated is the default/recommended)
            action_names = [
                "transcribe_annotated",
                "transcribe_formatted",
                "transcribe_basic",
                "transcribe_deep",
            ]
            run_mcp_server(mcp_mode, proxy_to=None, tool_names=action_names)
        sys.exit(0)

    # Validate that URL is provided for transcription
    if not args.url:
        parser.error("URL is required unless --mcp is specified")

    # Handle transcription
    try:
        # Build options from command line arguments
        # Default to annotated preset if no preset is specified
        if not any([args.basic, args.formatted, args.annotated, args.deep]):
            options = TranscribeOptions.annotated()
        else:
            options = TranscribeOptions.basic()  # Start with basic for explicit presets

        # Apply presets
        if args.basic:
            options = options.merge_with(TranscribeOptions.basic())
        if args.formatted:
            options = options.merge_with(TranscribeOptions.formatted())
        if args.annotated:
            options = options.merge_with(TranscribeOptions.annotated())
        if args.deep:
            options = options.merge_with(TranscribeOptions.deep())

        # Apply --with flags
        if args.with_flags:
            with_options = TranscribeOptions.from_with_flags(args.with_flags)
            options = options.merge_with(with_options)

        md_path, html_path = run_transcription(
            Path(args.workspace).resolve(),
            args.url,
            options,
            args.language,
            args.no_minify,
        )
        display_results(Path(args.workspace), md_path, html_path)
    except Exception as e:
        log.error("Error running deep transcription", exc_info=e)
        rprint(f"[red]Error: {e}[/red]")

        from kash.config.logger import get_log_settings

        log_file = get_log_settings().log_file_path
        rprint(f"[bright_black]See logs for more details: {fmt_path(log_file)}[/bright_black]")
        sys.exit(1)


if __name__ == "__main__":
    main()
