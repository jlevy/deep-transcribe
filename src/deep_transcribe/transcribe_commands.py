from __future__ import annotations

import logging
from pathlib import Path

from kash.exec import kash_action
from kash.exec.preconditions import is_audio_resource, is_url_resource, is_video_resource
from kash.model import Item
from kash.model.params_model import common_params

from deep_transcribe.transcribe_options import TranscribeOptions

log = logging.getLogger(__name__)


def transcribe_with_options(item: Item, options: TranscribeOptions, language: str = "en") -> Item:
    """Apply transcription processing steps based on the provided options."""
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

    result = transcribe(item, language=language)

    if options.format:
        if options.identify_speakers:
            result = identify_speakers(result)

        result = strip_html(result)
        result = break_into_paragraphs(result)
        result = backfill_timestamps(result)

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


@kash_action(
    precondition=is_url_resource | is_audio_resource | is_video_resource,
    params=common_params("language"),
    mcp_tool=True,
)
def transcribe_basic(item: Item, language: str = "en") -> Item:
    """Basic transcription (just transcription, no formatting or annotations)."""
    return transcribe_with_options(item, TranscribeOptions.basic(), language=language)


@kash_action(
    precondition=is_url_resource | is_audio_resource | is_video_resource,
    params=common_params("language"),
    mcp_tool=True,
)
def transcribe_formatted(item: Item, language: str = "en") -> Item:
    """Formatted transcription with speaker identification, paragraphs, and timestamps."""
    return transcribe_with_options(item, TranscribeOptions.formatted(), language=language)


@kash_action(
    precondition=is_url_resource | is_audio_resource | is_video_resource,
    params=common_params("language"),
    mcp_tool=True,
)
def transcribe_annotated(item: Item, language: str = "en") -> Item:
    """Annotated transcription with sections, summaries, descriptions, and frame captures."""
    return transcribe_with_options(item, TranscribeOptions.annotated(), language=language)


@kash_action(
    precondition=is_url_resource | is_audio_resource | is_video_resource,
    params=common_params("language"),
    mcp_tool=True,
)
def transcribe_deep(item: Item, language: str = "en") -> Item:
    """Deep transcription with all processing steps including research annotations."""
    return transcribe_with_options(item, TranscribeOptions.deep(), language=language)


def run_transcription(
    ws_root: Path, url: str, options: TranscribeOptions, language: str, no_minify: bool = False
) -> tuple[Path, Path]:
    """Transcribe the audio or video at the given URL using kash with the specified options."""
    from kash.config.unified_live import get_unified_live
    from kash.exec import kash_runtime, prepare_action_input

    ws_path = ws_root / "workspace"

    with kash_runtime(ws_path) as runtime:
        runtime.workspace.log_workspace_info()

        with get_unified_live().status("Processing…"):
            action_input = prepare_action_input(url)
            result_item = transcribe_with_options(action_input.items[0], options, language=language)

            return format_results(result_item, runtime.workspace.base_dir, no_minify=no_minify)


def format_results(result_item: Item, base_dir: Path, no_minify: bool = False) -> tuple[Path, Path]:
    """Format transcription results into HTML and return (markdown_path, html_path)."""
    from kash.model import Format, ItemType
    from kash.web_gen.template_render import render_web_template
    from kash.workspaces.workspaces import current_ws
    from strif import atomic_output_file

    html_content = render_web_template(
        "simple_webpage.html.jinja",
        data={
            "title": result_item.title,
            "add_title_h1": True,
            "content_html": result_item.body_as_html(),
            "thumbnail_url": result_item.thumbnail_url,
            "enable_themes": True,
            "show_theme_toggle": False,
        },
    )

    # Optionally minify the HTML.
    if not no_minify:
        from kash.actions.core.minify_html import minify_html

        raw_html_item = result_item.derived_copy(
            type=ItemType.export, format=Format.html, body=html_content
        )
        current_ws().save(raw_html_item)
        minified_item = minify_html(raw_html_item)
        html_content = minified_item.body

    # Save the final HTML item to the workspace.
    html_item = result_item.derived_copy(
        type=ItemType.export, format=Format.html, body=html_content
    )
    current_ws().save(html_item)

    if not result_item.store_path:
        raise ValueError("Transcription result has no store path")
    if not html_item.store_path:
        raise ValueError("HTML result has no store path")
    if not html_content:
        raise ValueError("HTML content is empty")

    md_path = base_dir / Path(result_item.store_path)
    html_path = base_dir / Path(html_item.store_path)

    with atomic_output_file(html_path) as tmp_path:
        tmp_path.write_text(html_content)

    return md_path, html_path
