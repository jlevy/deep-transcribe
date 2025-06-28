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
from flowmark import first_sentence
from kash.config.settings import DEFAULT_MCP_SERVER_PORT
from prettyfmt import fmt_path
from rich import print as rprint

from deep_transcribe.cli_commands import TRANSCRIBE_COMMANDS, run_transcription

log = logging.getLogger(__name__)

APP_NAME = "deep-transcribe"

DESCRIPTION = """High-quality transcription, formatting, and analysis of videos and podcasts"""

DEFAULT_WS = "./transcriptions"


def get_app_version() -> str:
    try:
        return "v" + version(APP_NAME)
    except Exception:
        return "unknown"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        formatter_class=ReadableColorFormatter,
        epilog=dedent((__doc__ or "") + "\n\n" + f"{APP_NAME} {get_app_version()}"),
        description=DESCRIPTION,
    )
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {get_app_version()}")

    # Common arguments for all actions.
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

    # Parsers for each action.
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Get actions for help text
    for name, func in TRANSCRIBE_COMMANDS.items():
        subparser = subparsers.add_parser(
            name,
            help=first_sentence(func.__doc__ or ""),
            description=func.__doc__,
            formatter_class=ReadableColorFormatter,
        )
        subparser.add_argument("url", type=str, help="URL of the video or audio to transcribe")
        subparser.add_argument(
            "--no_minify",
            action="store_true",
            help="Skip HTML/CSS/JS/Tailwind minification step.",
        )

    subparser = subparsers.add_parser(name="mcp", help="Run as an MCP server.")
    subparser.add_argument(
        "--sse",
        action="store_true",
        help=f"Run as an SSE MCP server at: http://127.0.0.1:{DEFAULT_MCP_SERVER_PORT}",
    )
    subparser.add_argument(
        "--logs",
        action="store_true",
        help="Just tail the logs from the MCP server in the terminal (good for debugging).",
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

    # Run as an MCP server.
    if args.subcommand == "mcp":
        from kash.mcp.mcp_main import McpMode, run_mcp_server
        from kash.mcp.mcp_server_commands import mcp_logs

        if args.logs:
            mcp_logs(follow=True, all=True)
        else:
            mcp_mode = McpMode.standalone_sse if args.sse else McpMode.standalone_stdio
            action_names = list(TRANSCRIBE_COMMANDS.keys())
            run_mcp_server(mcp_mode, proxy_to=None, tool_names=action_names)
        sys.exit(0)

    # Handle regular transcription.
    try:
        # Validate command
        if args.subcommand not in TRANSCRIBE_COMMANDS:
            raise ValueError(f"Unknown command: {args.subcommand}")

        md_path, html_path = run_transcription(
            args.subcommand,
            Path(args.workspace).resolve(),
            args.url,
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
