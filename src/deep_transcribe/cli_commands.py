from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kash.model import Item

log = logging.getLogger(__name__)


def transcribe_basic(url: str, language: str = "en") -> Item:
    """
    Download and transcribe audio from a podcast or video and return raw text,
    including timestamps if available (as HTML `<span>` tags), also caching
    video, audio, and transcript as local files.
    """
    from kash.exec import prepare_action_input
    from kash.kits.media.actions.transcribe.transcribe import transcribe

    input = prepare_action_input(url)
    return transcribe(input.items[0], language=language)


def transcribe_format(url: str, language: str = "en") -> Item:
    """
    In addition to basic transcription, attempt to identify the speakers, break text into
    paragraphs and if possible adding timestamps with links per paragraph.
    """
    from kash.exec import prepare_action_input
    from kash.kits.media.actions.transcribe.transcribe_format import transcribe_format

    input = prepare_action_input(url)
    return transcribe_format(input.items[0], language=language)


def transcribe_annotate(url: str, language: str = "en") -> Item:
    """
    In addition to formatted transcription, add sections, paragraph
    annotations, frame captures (avoiding duplicative frames), a bulleted
    summary, and a description at the top.
    """
    from kash.exec import prepare_action_input
    from kash.kits.media.actions.transcribe.transcribe_annotate import transcribe_annotate

    input = prepare_action_input(url)
    return transcribe_annotate(input.items[0], language=language)


TRANSCRIBE_COMMANDS = {
    "basic": transcribe_basic,
    "formatted": transcribe_format,
    "annotated": transcribe_annotate,
}


def run_transcription(
    command_name: str, ws_path: Path, url: str, language: str, no_minify: bool = False
) -> tuple[Path, Path]:
    """
    Transcribe the audio or video at the given URL using kash, which uses yt_dlp and
    Deepgram or Whisper APIs. URL must be to a supported platform, which include
    YouTube or Apple Podcasts.
    """
    from kash.config.setup import kash_setup
    from kash.exec import kash_runtime

    # Set up kash workspace.
    kash_setup(kash_ws_root=ws_path.parent, rich_logging=True)

    # Run all actions in the context of this workspace.
    with kash_runtime(ws_path) as runtime:
        # Show the user the workspace info.
        runtime.workspace.log_workspace_info()

        # Run the action using the appropriate wrapper function.
        if command_name not in TRANSCRIBE_COMMANDS:
            raise ValueError(f"Unknown command: {command_name}")

        command_func = TRANSCRIBE_COMMANDS[command_name]
        result_item = command_func(url, language=language)

        return format_results(result_item, runtime.workspace.base_dir, no_minify=no_minify)


def format_results(result_item: Item, base_dir: Path, no_minify: bool = False) -> tuple[Path, Path]:
    """
    Format the results of a transcription.
    """
    from kash.actions.core.minify_html import minify_html
    from kash.actions.core.tabbed_webpage_config import tabbed_webpage_config
    from kash.actions.core.tabbed_webpage_generate import tabbed_webpage_generate
    from kash.model import ActionInput

    # These are regular actions that require ActionInput/ActionResult.
    config = tabbed_webpage_config(ActionInput(items=[result_item]))
    html_result = tabbed_webpage_generate(ActionInput(items=config.items))
    if not no_minify:
        minified_result = minify_html(html_result.items[0])
    else:
        minified_result = html_result.items[0]

    assert result_item.store_path
    assert minified_result.store_path

    md_path = base_dir / Path(result_item.store_path)
    html_path = base_dir / Path(minified_result.store_path)

    return md_path, html_path
