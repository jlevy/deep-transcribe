import argparse
import sys
from importlib.metadata import version
from pathlib import Path
from textwrap import dedent
from typing import Any

from flowmark import first_sentence
from kash.kits.media.actions.deep_transcribe import deep_transcribe
from kash.kits.media.actions.transcribe_format import transcribe_and_format
from kash.shell import shell_main
from prettyfmt import fmt_path
from rich import print as rprint
from rich_argparse.contrib import ParagraphRichHelpFormatter

from deep_transcribe.transcription import run_transcription

APP_NAME = "deep_transcribe"


def get_app_version() -> str:
    try:
        return "v" + version(APP_NAME)
    except Exception:
        return "unknown"


def build_parser() -> argparse.ArgumentParser:
    class CustomFormatter(ParagraphRichHelpFormatter):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, width=88, **kwargs)

    parser = argparse.ArgumentParser(
        formatter_class=CustomFormatter,
        description=f"{APP_NAME} {get_app_version()}",
    )
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {get_app_version()}")

    # Common arguments for all actions.
    parser.add_argument(
        "--workspace",
        type=str,
        default="deep_transcribe",
        help="The workspace directory to use for files, metadata, and cache",
    )
    parser.add_argument(
        "--language",
        type=str,
        default="en",
        help="Language of the video or audio to transcribe",
    )
    parser.add_argument(
        "--rerun", action="store_true", help="Rerun actions even if the outputs already exist"
    )

    # Parsers for each action.
    subparsers = parser.add_subparsers(dest="action", required=True)

    subparsers.add_parser(
        "deep",
        help=first_sentence(deep_transcribe.__doc__ or ""),
        description=deep_transcribe.__doc__,
        formatter_class=CustomFormatter,
    ).add_argument("url", type=str, help="URL of the video or audio to transcribe")

    subparsers.add_parser(
        "basic",
        help=first_sentence(transcribe_and_format.__doc__ or ""),
        description=transcribe_and_format.__doc__,
        formatter_class=CustomFormatter,
    ).add_argument("url", type=str, help="URL of the video or audio to transcribe")

    subparsers.add_parser(
        "kash",
        help="Launch the kash shell with all tools loaded.",
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
    args = build_parser().parse_args()

    # Option to run the kash shell with media tools loaded.
    if args.action == "kash":
        rprint("[bright_black]Running kash shell with media tools loaded...[/bright_black]")
        sys.exit(shell_main.run_shell())
    else:
        # Handle regular transcription.
        md_path, html_path = run_transcription(
            Path(args.workspace), args.url, args.language, args.action
        )
        display_results(Path(args.workspace), md_path, html_path)


if __name__ == "__main__":
    main()
