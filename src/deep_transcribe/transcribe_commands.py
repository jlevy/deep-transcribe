from __future__ import annotations

import logging
from pathlib import Path

# Keep kash imports minimal initially.
from kash.exec import kash_action
from kash.exec.preconditions import is_audio_resource, is_url_resource, is_video_resource
from kash.model import Item, Param
from kash.model.params_model import common_params

from deep_transcribe.transcribe_options import TranscribeOptions
from deep_transcribe.transcription_metadata import (
    TranscriptionMetadata,
    apply_transcription_metadata,
    copy_source_metadata,
    get_speaker_roster,
    parse_transcription_metadata,
    persist_item_metadata,
)

log = logging.getLogger(__name__)


def transcribe_with_options(
    item: Item,
    options: TranscribeOptions,
    language: str = "en",
    transcription_model: str = "nova-3",
    diarize_model: str = "latest",
    *,
    rerun_processing: bool = False,
) -> Item:
    """
    Apply transcription processing steps to an item based on provided options.
    """
    from kash.kits.media.actions.transcribe.transcribe import transcribe
    from kash.kits.media.transcription_context import get_transcription_metadata
    from kash.workspaces import current_ws

    key_terms = "\n".join(get_transcription_metadata(item).get("key_terms", []))
    result = transcribe(
        item,
        language=language,
        transcription_model=transcription_model,
        diarize_model=diarize_model,
        key_terms=key_terms,
    )

    # A raw transcription cache hit can predate newly supplied descriptive metadata.
    # Refresh only its metadata so later semantic action hashes see the correction.
    old_metadata = result.metadata()
    copy_source_metadata(item, result)
    if result.metadata() != old_metadata:
        current_ws().save(result, overwrite=True)

    if rerun_processing:
        from kash.exec import kash_runtime

        with kash_runtime(current_ws().base_dir, rerun=True):
            return _process_transcript(result, options)
    return _process_transcript(result, options)


def _process_transcript(result: Item, options: TranscribeOptions) -> Item:
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

    # Apply formatting pipeline if requested
    if options.format:
        # Speaker identification (if requested)
        if options.identify_speakers:
            if get_speaker_roster(result):
                from deep_transcribe.speaker_correction import correct_speaker_turns

                result = correct_speaker_turns(result)
            else:
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


TRANSCRIPTION_ACTION_PARAMS = common_params("language") + (
    Param(
        "transcription_model",
        "Deepgram speech-to-text model.",
        type=str,
        default_value="nova-3",
    ),
    Param(
        "diarize_model",
        "Deepgram speaker diarization model.",
        type=str,
        default_value="latest",
    ),
    Param(
        "metadata_yaml",
        (
            "Inline YAML or JSON source metadata. Supports title, description, "
            "additional_context, key_terms, speaker_hints, speaker_roster, and extra."
        ),
        type=str,
        default_value="",
    ),
)


def _transcribe_preset(
    item: Item,
    options: TranscribeOptions,
    *,
    language: str,
    transcription_model: str,
    diarize_model: str,
    metadata_yaml: str,
) -> Item:
    if metadata_yaml.strip():
        apply_transcription_metadata(item, parse_transcription_metadata(metadata_yaml))
    return transcribe_with_options(
        item,
        options,
        language=language,
        transcription_model=transcription_model,
        diarize_model=diarize_model,
    )


@kash_action(
    precondition=is_url_resource | is_audio_resource | is_video_resource,
    params=TRANSCRIPTION_ACTION_PARAMS,
    mcp_tool=True,
)
def transcribe_basic(
    item: Item,
    language: str = "en",
    transcription_model: str = "nova-3",
    diarize_model: str = "latest",
    metadata_yaml: str = "",
) -> Item:
    """
    Transcribe without LLM formatting or annotations.
    """
    return _transcribe_preset(
        item,
        TranscribeOptions.basic(),
        language=language,
        transcription_model=transcription_model,
        diarize_model=diarize_model,
        metadata_yaml=metadata_yaml,
    )


@kash_action(
    precondition=is_url_resource | is_audio_resource | is_video_resource,
    params=TRANSCRIPTION_ACTION_PARAMS,
    mcp_tool=True,
)
def transcribe_formatted(
    item: Item,
    language: str = "en",
    transcription_model: str = "nova-3",
    diarize_model: str = "latest",
    metadata_yaml: str = "",
) -> Item:
    """
    Transcribe, identify speakers, and format paragraphs and timestamps.
    """
    return _transcribe_preset(
        item,
        TranscribeOptions.formatted(),
        language=language,
        transcription_model=transcription_model,
        diarize_model=diarize_model,
        metadata_yaml=metadata_yaml,
    )


@kash_action(
    precondition=is_url_resource | is_audio_resource | is_video_resource,
    params=TRANSCRIPTION_ACTION_PARAMS,
    mcp_tool=True,
)
def transcribe_annotated(
    item: Item,
    language: str = "en",
    transcription_model: str = "nova-3",
    diarize_model: str = "latest",
    metadata_yaml: str = "",
) -> Item:
    """
    Transcribe and add formatting, sections, summary, description, and frames.
    """
    return _transcribe_preset(
        item,
        TranscribeOptions.annotated(),
        language=language,
        transcription_model=transcription_model,
        diarize_model=diarize_model,
        metadata_yaml=metadata_yaml,
    )


@kash_action(
    precondition=is_url_resource | is_audio_resource | is_video_resource,
    params=TRANSCRIPTION_ACTION_PARAMS,
    mcp_tool=True,
)
def transcribe_deep(
    item: Item,
    language: str = "en",
    transcription_model: str = "nova-3",
    diarize_model: str = "latest",
    metadata_yaml: str = "",
) -> Item:
    """
    Run the complete transcription pipeline, including research annotations.
    """
    return _transcribe_preset(
        item,
        TranscribeOptions.deep(),
        language=language,
        transcription_model=transcription_model,
        diarize_model=diarize_model,
        metadata_yaml=metadata_yaml,
    )


def run_transcription(
    ws_root: Path,
    url: str,
    options: TranscribeOptions,
    language: str,
    *,
    transcription_model: str = "nova-3",
    diarize_model: str = "latest",
    metadata: TranscriptionMetadata | None = None,
    no_minify: bool = False,
    rerun: bool = False,
    rerun_processing: bool = False,
) -> tuple[Path, Path]:
    """
    Transcribe the audio or video at the given URL using kash with the specified options.

    Args:
        ws_root: Root directory for the workspace
        url: URL of the video or audio to transcribe
        options: TranscribeOptions instance specifying processing steps
        language: Language code for transcription
        transcription_model: Deepgram speech-to-text model
        diarize_model: Deepgram speaker diarization model
        metadata: Optional metadata to add to the source before transcription
        no_minify: If True, skip HTML minification
        rerun: If True, rerun every action, including raw transcription
        rerun_processing: If True, rerun post-transcription processing only

    Returns:
        Tuple of (transcript_path, html_path) for the generated files
    """
    # Import dynamically for faster startup.
    from kash.config.setup import kash_setup
    from kash.config.unified_live import get_unified_live
    from kash.exec import kash_runtime, prepare_action_input

    # Set up kash workspace.
    kash_setup(kash_ws_root=ws_root, rich_logging=True)
    ws_path = ws_root / "workspace"

    # Run all actions in the context of this workspace.
    with kash_runtime(ws_path, rerun=rerun) as runtime:
        # Show the user the workspace info.
        runtime.workspace.log_workspace_info()

        with get_unified_live().status("Processing…"):
            action_input = prepare_action_input(url)
            item = action_input.items[0]
            source_item = item
            source_metadata_changed = False

            # Generic web fetches may return the downloaded content rather than the URL
            # resource required by the media transcription action.
            if not is_url_resource(item) and item.url:
                from kash.model import Format, ItemType

                url_item = item.new_copy_with(
                    type=ItemType.resource,
                    format=Format.url,
                    body=None,
                    external_path=None,
                )
                if found_path := runtime.workspace.find_by_id(url_item):
                    item = runtime.workspace.load(found_path)
                    old_metadata = item.metadata()
                    copy_source_metadata(source_item, item)
                    source_metadata_changed = item.metadata() != old_metadata
                else:
                    runtime.workspace.save(url_item)
                    item = url_item

            old_metadata = item.metadata()
            if metadata:
                apply_transcription_metadata(item, metadata)
            if source_metadata_changed or item.metadata() != old_metadata:
                persist_item_metadata(item, runtime.workspace)

            result_item = transcribe_with_options(
                item,
                options,
                language=language,
                transcription_model=transcription_model,
                diarize_model=diarize_model,
                rerun_processing=rerun_processing,
            )

            return format_results(result_item, runtime.workspace.base_dir, no_minify=no_minify)


def format_results(result_item: Item, base_dir: Path, no_minify: bool = False) -> tuple[Path, Path]:
    """
    Format the results of a transcription into HTML and ensure proper file paths.

    Args:
        result_item: The transcription result item
        base_dir: Base directory for output files
        no_minify: If True, skip HTML minification

    Returns:
        Tuple of (transcript_path, html_path) for the generated files
    """
    # Import dynamically for faster startup.
    from kash.actions.core.minify_html import minify_html
    from kash.model import Format, ItemType
    from kash.web_gen.webpage_render import render_item_as_html
    from kash.workspaces.workspaces import current_ws

    raw_html_item = result_item.derived_copy(
        type=ItemType.export,
        format=Format.html,
    )
    raw_html_item = render_item_as_html(
        result_item,
        raw_html_item,
        add_title_h1=True,
        template_filename="simple_webpage.html.jinja",
    )
    current_ws().save(raw_html_item)

    if not no_minify:
        html_item = minify_html(raw_html_item)
    else:
        html_item = raw_html_item

    assert result_item.store_path
    assert html_item.store_path
    assert html_item.body

    transcript_path = base_dir / Path(result_item.store_path)
    html_path = base_dir / Path(html_item.store_path)

    return transcript_path, html_path


## Tests


def test_format_results_copies_frame_assets() -> None:
    from tempfile import TemporaryDirectory

    from kash.exec import kash_runtime
    from kash.model import Format, ItemType
    from kash.workspaces import current_ws
    from sidematter_format import Sidematter
    from strif import atomic_output_file

    with TemporaryDirectory() as temp_dir:
        workspace_dir = Path(temp_dir) / "workspace"
        with kash_runtime(workspace_dir):
            ws = current_ws()
            result_item = Item(
                type=ItemType.doc,
                format=Format.md_html,
                title="Transcript with frames",
            )
            source_path = ws.assign_store_path(result_item)
            source_assets = Sidematter(source_path).assets_dir
            result_item.body = f'<img src="{source_assets.name}/frame.jpg" alt="Frame">'
            ws.save(result_item)

            frame_path = source_assets / "frame.jpg"
            with atomic_output_file(frame_path, make_parents=True) as temp_path:
                temp_path.write_bytes(b"frame")

            transcript_path, html_path = format_results(
                result_item,
                ws.base_dir,
                no_minify=True,
            )

            html_assets = Sidematter(html_path).assets_dir
            assert transcript_path == source_path
            assert f"{html_assets.name}/frame.jpg" in html_path.read_text()
            assert (html_assets / "frame.jpg").read_bytes() == b"frame"
