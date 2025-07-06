from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from deep_transcribe.transcribe_options import TranscribeOptions

if TYPE_CHECKING:
    from kash.exec import kash_action
    from kash.exec.preconditions import is_audio_resource, is_url_resource, is_video_resource
    from kash.model import Item
    from kash.model.params_model import common_params


log = logging.getLogger(__name__)


def transcribe_with_options(item: Item, options: TranscribeOptions, language: str = "en") -> Item:
    """
    Apply transcription processing steps to an item based on provided options.
    """
    # Import dynamically for faster startup.
    from kash.actions.core.strip_html import strip_html
    from kash.kits.docs.actions.text.add_description import add_description
    from kash.kits.docs.actions.text.add_summary_bullets import add_summary_bullets
    from kash.kits.docs.actions.text.break_into_paragraphs import break_into_paragraphs
    from kash.kits.docs.actions.text.insert_section_headings import insert_section_headings
    from kash.kits.docs.actions.text.research_paras import research_paras
    from kash.kits.media.actions.transcribe.backfill_timestamps import backfill_timestamps
    from kash.kits.media.actions.transcribe.identify_speakers import identify_speakers
    from kash.kits.media.actions.transcribe.insert_frame_captures import insert_frame_captures
    from kash.kits.media.actions.transcribe.transcribe import transcribe

    # Start with basic transcription
    result = transcribe(item, language=language)

    # Apply formatting pipeline if requested
    if options.format:
        # Speaker identification (if requested)
        if options.identify_speakers:
            result = identify_speakers(result)

        result = strip_html(result)
        result = break_into_paragraphs(result)
        result = backfill_timestamps(result)

    # Apply annotation pipeline if requested
    if options.insert_section_headings:
        result = insert_section_headings(result)

    if options.research_paras:
        result = research_paras(result)

    if options.add_summary_bullets:
        result = add_summary_bullets(result)

    if options.add_description:
        result = add_description(result)

    if options.insert_frame_captures:
        result = insert_frame_captures(result)

    return result


# Import kash decorator dependencies when needed
from kash.exec import kash_action
from kash.exec.preconditions import is_audio_resource, is_url_resource, is_video_resource
from kash.model import Item
from kash.model.params_model import common_params


@kash_action(
    precondition=is_url_resource | is_audio_resource | is_video_resource,
    params=common_params("language"),
    mcp_tool=True,
)
def transcribe_basic(item: Item, language: str = "en") -> Item:
    """
    Basic transcription (just transcription, no formatting or annotations).

    Args:
        item: Input item (URL, audio, or video resource)
        language: Language code for transcription (default: "en")

    Returns:
        Item: The basic transcription result
    """
    return transcribe_with_options(item, TranscribeOptions.basic(), language=language)


@kash_action(
    precondition=is_url_resource | is_audio_resource | is_video_resource,
    params=common_params("language"),
    mcp_tool=True,
)
def transcribe_formatted(item: Item, language: str = "en") -> Item:
    """
    Formatted transcription (transcription + formatting, recommended).

    Args:
        item: Input item (URL, audio, or video resource)
        language: Language code for transcription (default: "en")

    Returns:
        Item: The formatted transcription result
    """
    return transcribe_with_options(item, TranscribeOptions.formatted(), language=language)


@kash_action(
    precondition=is_url_resource | is_audio_resource | is_video_resource,
    params=common_params("language"),
    mcp_tool=True,
)
def transcribe_annotated(item: Item, language: str = "en") -> Item:
    """
    Annotated transcription (full processing except research).

    Args:
        item: Input item (URL, audio, or video resource)
        language: Language code for transcription (default: "en")

    Returns:
        Item: The annotated transcription result
    """
    return transcribe_with_options(item, TranscribeOptions.annotated(), language=language)


@kash_action(
    precondition=is_url_resource | is_audio_resource | is_video_resource,
    params=common_params("language"),
    mcp_tool=True,
)
def transcribe_deep(item: Item, language: str = "en") -> Item:
    """
    Deep transcription (complete processing including research).

    Args:
        item: Input item (URL, audio, or video resource)
        language: Language code for transcription (default: "en")

    Returns:
        Item: The deep transcription result with all features
    """
    return transcribe_with_options(item, TranscribeOptions.deep(), language=language)


def run_transcription(
    ws_root: Path, url: str, options: TranscribeOptions, language: str, no_minify: bool = False
) -> tuple[Path, Path]:
    """
    Transcribe the audio or video at the given URL using kash with the specified options.

    Args:
        ws_root: Root directory for the workspace
        url: URL of the video or audio to transcribe
        options: TranscribeOptions instance specifying processing steps
        language: Language code for transcription
        no_minify: If True, skip HTML minification

    Returns:
        Tuple of (markdown_path, html_path) for the generated files
    """
    # Import dynamically for faster startup.
    from kash.config.setup import kash_setup
    from kash.exec import kash_runtime, prepare_action_input

    # Set up kash workspace.
    kash_setup(kash_ws_root=ws_root, rich_logging=True)
    ws_path = ws_root / "workspace"

    # Run all actions in the context of this workspace.
    with kash_runtime(ws_path) as runtime:
        # Show the user the workspace info.
        runtime.workspace.log_workspace_info()

        # Prepare the URL input and run transcription.
        input = prepare_action_input(url)
        result_item = transcribe_with_options(input.items[0], options, language=language)

        return format_results(result_item, runtime.workspace.base_dir, no_minify=no_minify)


def format_results(result_item: Item, base_dir: Path, no_minify: bool = False) -> tuple[Path, Path]:
    """
    Format the results of a transcription into HTML and ensure proper file paths.

    Args:
        result_item: The transcription result item
        base_dir: Base directory for output files
        no_minify: If True, skip HTML minification

    Returns:
        Tuple of (markdown_path, html_path) for the generated files
    """
    # Import dynamically for faster startup.
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
