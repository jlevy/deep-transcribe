import logging
from enum import Enum
from pathlib import Path

from kash.actions.core.webpage_config import webpage_config
from kash.actions.core.webpage_generate import webpage_generate
from kash.exec import prepare_action_input
from kash.kits.media.actions.transcribe import transcribe
from kash.kits.media.actions.transcribe_annotate import transcribe_annotate
from kash.kits.media.actions.transcribe_format import transcribe_format
from kash.model import ActionInput, Item
from kash.workspaces import get_ws
from kash.workspaces.workspaces import switch_to_ws

log = logging.getLogger(__name__)


class TranscriptionType(Enum):
    transcribe = "transcribe"
    """Raw transcription, with timestamps."""

    transcribe_format = "transcribe_format"
    """Formatting of the transcription as paragraphs."""

    transcribe_annotate = "transcribe_annotate"
    """Fully processed transcription with section headers and annotations, etc."""


def run_transcription(
    transcription_type: TranscriptionType,
    ws_path: Path,
    url: str,
    language: str,
) -> tuple[Path, Path]:
    """
    Transcribe the audio or video at the given URL using kash, which uses yt_dlp and
    Deepgram or Whisper APIs. URL must be to a supported platform, which include
    YouTube or Apple Podcasts.
    """

    # Get the workspace.
    ws = get_ws(ws_path)
    log.warning("Switching to workspace: %s", ws.base_dir)
    switch_to_ws(ws.base_dir)

    # Show the user the workspace info.
    ws.log_workspace_info()

    # Run all actions in the context of this workspace.
    with ws:
        # This adds the resource to the workspace and fetches any metadata.
        input = prepare_action_input(url)

        # Run the action.
        if transcription_type == TranscriptionType.transcribe:
            result_item = transcribe(input.items[0], language=language)
        elif transcription_type == TranscriptionType.transcribe_format:
            result_item = transcribe_format(input.items[0], language=language)
        elif transcription_type == TranscriptionType.transcribe_annotate:
            result_item = transcribe_annotate(input.items[0], language=language)
        else:
            raise ValueError(f"Unknown transcription type: {transcription_type}")

        return format_results(result_item, ws.base_dir)


def format_results(result_item: Item, base_dir: Path) -> tuple[Path, Path]:
    """
    Format the results of a transcription.
    """
    # These are regular actions that require ActionInput/ActionResult.
    config = webpage_config(ActionInput(items=[result_item]))
    html_final = webpage_generate(ActionInput(items=config.items))

    assert result_item.store_path
    assert html_final.items[0].store_path

    md_path = base_dir / Path(result_item.store_path)
    html_path = base_dir / Path(html_final.items[0].store_path)

    return md_path, html_path
