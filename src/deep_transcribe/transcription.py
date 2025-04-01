from pathlib import Path
from typing import Literal, TypeAlias

from kash.actions.core.webpage_config import webpage_config
from kash.actions.core.webpage_generate import webpage_generate
from kash.exec import prepare_action_input
from kash.kits.media.actions.deep_transcribe import deep_transcribe
from kash.kits.media.actions.transcribe_format import transcribe_and_format
from kash.model import ActionInput, Item
from kash.workspaces import get_ws

TranscriptionType: TypeAlias = Literal["deep", "basic"]


def run_transcription(
    ws_path: Path,
    url: str,
    language: str,
    transcription_type: TranscriptionType,
) -> tuple[Path, Path]:
    # Get the workspace.
    ws = get_ws(ws_path)

    # Show the user the workspace info.
    ws.log_workspace_info()

    # Run all actions in the context of this workspace.
    with ws:
        # This adds the resource to the workspace and fetches any metadata.
        input = prepare_action_input(url)

        # Run the action.
        if transcription_type == "deep":
            result_item = deep_transcribe(input.items[0], language=language)
        elif transcription_type == "basic":
            result_item = transcribe_and_format(input.items[0], language=language)
        else:
            raise ValueError(f"Unknown action: {transcription_type}")

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
