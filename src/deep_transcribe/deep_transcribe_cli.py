import argparse
import sys
from importlib.metadata import version
from pathlib import Path
from textwrap import dedent

from flowmark import first_sentence
from kash.config.settings import DEFAULT_MCP_SERVER_PORT
from kash.kits.media.actions.transcribe import transcribe
from kash.kits.media.actions.transcribe_annotate import transcribe_annotate
from kash.kits.media.actions.transcribe_format import transcribe_format
from kash.mcp.mcp_main import McpMode, run_mcp_server
from kash.mcp.mcp_server_commands import mcp_logs
from kash.shell import shell_main
from kash.shell.utils.argparse_utils import WrappedColorFormatter
from prettyfmt import fmt_path
from rich import print as rprint

from deep_transcribe.transcription import TranscriptionType, run_transcription

APP_NAME = "deep_transcribe"

DEFAULT_WS = "./transcriptions"

TRANSCRIBE_ACTIONS = [
    transcribe,
    transcribe_format,
    transcribe_annotate,
]


def get_app_version() -> str:
    try:
        return "v" + version(APP_NAME)
    except Exception:
        return "unknown"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        formatter_class=WrappedColorFormatter,
        description=f"{APP_NAME} {get_app_version()}",
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

    for func in TRANSCRIBE_ACTIONS:
        subparser = subparsers.add_parser(
            func.__name__,
            help=first_sentence(func.__doc__ or ""),
            description=func.__doc__,
            formatter_class=WrappedColorFormatter,
        )
        subparser.add_argument("url", type=str, help="URL of the video or audio to transcribe")

    subparser = subparsers.add_parser(
        "kash",
        help="Launch the kash shell (a full command line environment with all transcription tools loaded).",
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


def display_results(base_dir: Path, md_path: Path, html_path: Path):
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
    parser = build_parser()
    args = parser.parse_args()

    # Run as an MCP server.
    if args.subcommand == "mcp":
        # Important we set up logging to do stderr not stdout for stdout server.
        if args.logs:
            mcp_logs(follow=True, all=True)
        else:
            mcp_mode = McpMode.standalone_sse if args.sse else McpMode.standalone_stdio
            action_names = [func.__name__ for func in TRANSCRIBE_ACTIONS]
            run_mcp_server(mcp_mode, proxy_to=None, tool_names=action_names)
        sys.exit(0)

    # Option to run the kash shell with media tools loaded.
    if args.subcommand == "kash":
        rprint("[bright_black]Running kash shell with media tools loaded...[/bright_black]")
        sys.exit(shell_main.run_shell())

    # Handle regular transcription.

    try:
        try:
            transcription_type = TranscriptionType(args.subcommand)
        except ValueError:
            raise ValueError(f"Unknown command: {args.subcommand}") from None
        md_path, html_path = run_transcription(
            transcription_type,
            Path(args.workspace).resolve(),
            args.url,
            args.language,
        )
        display_results(Path(args.workspace), md_path, html_path)
    except Exception as e:
        rprint(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
