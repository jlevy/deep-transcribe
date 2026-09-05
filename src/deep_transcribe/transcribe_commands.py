from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast

# Keep kash imports minimal initially.
from kash.exec import kash_action
from kash.exec.preconditions import (
    has_simple_text_body,
    is_audio_resource,
    is_url_resource,
    is_video_resource,
)
from kash.model import Item, Param
from kash.model.params_model import common_params

from deep_transcribe.disk_space import (
    check_download_space,
    check_frame_capture_space,
    source_duration,
)
from deep_transcribe.transcribe_options import TranscribeOptions
from deep_transcribe.transcription_metadata import (
    TranscriptionMetadata,
    apply_transcription_metadata,
    copy_source_metadata,
    get_speaker_roster,
    parse_transcription_metadata,
    persist_item_metadata,
    remove_processing_instructions,
    remove_replacements,
    remove_segment_hints,
    set_processing_instructions,
    set_replacements,
    set_segment_hints,
    strip_volatile_source_fields,
)

if TYPE_CHECKING:
    from kash.file_storage.file_store import FileStore
    from kash.model.paths_model import StorePath

    from deep_transcribe.segment_hints import SegmentHints
    from deep_transcribe.transcript_report import TranscriptReport

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class TranscriptionOutputs:
    """
    What a run produced: the two paths, and the report when one was asked for.

    The report has to be built where the final item still exists, so it is carried back
    with the paths rather than recomputed by the caller from a path.
    """

    transcript_path: Path
    html_path: Path
    report: TranscriptReport | None = None


class NoCachedResult(Exception):
    """
    No finished run for this source is stored in this workspace.

    A distinct type because the caller turns it into a usage error rather than a failure:
    asking to re-export what was never exported is a mistake about which workspace or
    which source, and the answer is one line, not a traceback.
    """


def _media_source_locator(source: str) -> str:
    """
    Represent local media as a file URL so kash caches it without first copying the
    entire source into the workspace.
    """
    source_path = Path(source).expanduser()
    if not source_path.is_file():
        return source

    from kash.utils.common.url import as_file_url

    return as_file_url(source_path)


def _prepare_source_item(source: str) -> Item:
    """Prepare media after registering Kash's optional service extractors."""
    from importlib import import_module

    from kash.exec import prepare_action_input

    import_module("kash.kits.media.media_services")

    locator = _media_source_locator(source)
    item = prepare_action_input(locator).items[0]
    if item.url and "media_service" not in (item.extra or {}):
        from kash.media_base.media_services import get_media_id

        if get_media_id(item.url):
            item = prepare_action_input(locator, refetch=True).items[0]
    return item


def _identify_transcript_speakers(result: Item, web_search: bool = False) -> Item:
    """Choose exact, inferred, or provider-level speaker identification."""
    from kash.kits.media.actions.transcribe.identify_speakers import identify_speakers

    # Source metadata is evidence on its own, so this runs without user-authored context.
    if not get_speaker_roster(result):
        from deep_transcribe.speaker_correction import infer_speaker_roster_from_context

        result = infer_speaker_roster_from_context(result, web_search=web_search)
    if get_speaker_roster(result):
        from deep_transcribe.speaker_correction import correct_speaker_turns

        return correct_speaker_turns(result)
    return identify_speakers(result)


@kash_action(
    precondition=has_simple_text_body,
    params=(
        Param(
            "processing_instructions",
            "Output-only instructions for transcript overview stages.",
            type=str,
        ),
        Param(
            "segment_hints",
            "Segment hints, as YAML text, marking stretches to set aside.",
            type=str,
        ),
    ),
)
def _attach_late_inputs(
    item: Item,
    *,
    processing_instructions: str | None,
    segment_hints: str | None = None,
) -> Item:
    """
    Create a cache boundary whose identity includes the analysis-only inputs.

    Everything above this line — transcription, speaker correction, paragraphs, section
    headings — keeps its identity when these change, and everything below is redone.
    That is what makes editing a segment hint or an instruction and rerunning cost
    minutes rather than the whole pipeline.
    """
    import yaml

    result = item.derived_copy(body=item.body)
    if processing_instructions is not None:
        set_processing_instructions(result, processing_instructions)
    if segment_hints:
        # Carried as YAML text rather than a mapping so the action's identity is a plain
        # string: two hint files that differ only in key order must hash the same.
        set_segment_hints(result, yaml.safe_load(segment_hints))
    return result


def _transcribe_raw(
    item: Item,
    *,
    language: str,
    transcription_model: str,
    diarize_model: str,
    key_terms: str,
) -> Item:
    """Run the lazily imported raw media transcription action."""
    from kash.kits.media.actions.transcribe.transcribe import transcribe

    return transcribe(
        item,
        language=language,
        transcription_model=transcription_model,
        diarize_model=diarize_model,
        key_terms=key_terms,
    )


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
    from kash.workspaces import current_ws

    workspace = current_ws()
    key_terms = "\n".join(TranscriptionMetadata(extra=item.extra or {}).key_terms)

    # Output-only instructions must not change the raw transcription action identity.
    # Hold them outside the cached transcription and speaker-formatting chain, then
    # restore them immediately before the overview stages that consume them.
    processing_instructions = remove_processing_instructions(item)
    segment_hints = remove_segment_hints(item)
    # Text replacements are read only by the correction stage below, so they get the same
    # treatment: held off the source for the raw request, then put back on the transcript.
    replacements = remove_replacements(item)
    if (
        processing_instructions is not None or segment_hints is not None or replacements
    ) and item.store_path is not None:
        # Kash hashes a stored input's file content when assembling an operation. Keep
        # the persisted source canonical too, or an in-memory removal alone cannot make
        # instruction-only reruns hit the raw action cache.
        persist_item_metadata(item, workspace)
    try:
        result = _transcribe_raw(
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
        remove_processing_instructions(result)
        # The mapping travels on the transcript rather than the resource, so changing it
        # re-runs the correction stage and everything below it, never speech-to-text.
        set_replacements(result, replacements)
        if result.metadata() != old_metadata:
            workspace.save(result, overwrite=True)
    finally:
        # The late inputs go back onto the stored resource so they stick to the item: a
        # later run without --instructions or --segments still honors what the user asked
        # for, which is the behaviour `test_processing_instructions_bypass_raw_and_formatting
        # _cache_identity` pins and what makes a "clear" affordance necessary at all.
        #
        # The cost is that a CHANGE to a late input alters the file kash hashes, so it
        # re-runs paragraph formatting and section headings. Measured on a fresh workspace:
        # an unchanged rerun is 5 s and free, while adding --segments re-runs those two
        # stages (13 and 30 minutes on the 5-hour recording). Resolving that needs the late
        # inputs stored outside the hashed metadata; tracked separately rather than traded
        # against stickiness here.
        set_processing_instructions(item, processing_instructions)
        if segment_hints is not None:
            set_segment_hints(item, segment_hints)
        set_replacements(item, replacements)
        if (
            processing_instructions is not None or segment_hints is not None or replacements
        ) and item.store_path is not None:
            persist_item_metadata(item, workspace)

    if rerun_processing:
        from kash.exec import kash_runtime

        with kash_runtime(workspace.base_dir, rerun=True):
            return _process_transcript(
                result,
                options,
                processing_instructions=processing_instructions,
                segment_hints=segment_hints,
            )
    return _process_transcript(
        result,
        options,
        processing_instructions=processing_instructions,
        segment_hints=segment_hints,
    )


def _process_transcript(
    result: Item,
    options: TranscribeOptions,
    *,
    processing_instructions: str | None,
    segment_hints: object = None,
) -> Item:
    # Import dynamically for faster startup.
    from kash.actions.core.strip_html import strip_html
    from kash.kits.docs.actions.text.break_into_paragraphs import break_into_paragraphs
    from kash.kits.docs.actions.text.insert_section_headings import insert_section_headings
    from kash.kits.docs.actions.text.research_paras import research_paras
    from kash.kits.media.actions.transcribe.backfill_timestamps import backfill_timestamps
    from kash.kits.media.actions.transcribe.insert_frame_captures import insert_frame_captures

    from deep_transcribe.timestamp_citations import normalize_timestamp_citations
    from deep_transcribe.transcript_overview import (
        add_transcript_description,
        add_transcript_outline,
    )
    from deep_transcribe.transcript_replacements import apply_replacements_if_any
    from deep_transcribe.transcript_spacing import (
        fold_back_channel_turns,
        normalize_transcript_fragments,
    )

    # Sanitize legacy raw-cache entries that may still carry output-only inputs.
    remove_processing_instructions(result)
    remove_segment_hints(result)

    # Deterministic corrections come first, so speaker correction, paragraphs, headings,
    # and the overview stages all read the corrected words.
    result = apply_replacements_if_any(result)

    # Apply formatting pipeline if requested
    if options.format:
        # Speaker identification (if requested)
        if options.identify_speakers:
            result = _identify_transcript_speakers(result, web_search=options.web_search)

        result = normalize_transcript_fragments(result)
        result = strip_html(result)
        result = break_into_paragraphs(result)
        if not options.keep_back_channel:
            # Paragraphs exist here but citations do not, so a folded turn simply stops
            # being a paragraph and stops earning a timestamp of its own.
            result = fold_back_channel_turns(result)
        result = backfill_timestamps(result)
        result = normalize_timestamp_citations(result)

    # Apply annotation pipeline if requested
    if options.insert_section_headings:
        result = insert_section_headings(result)

    if options.research_paras:
        result = research_paras(result)

    has_overview_stage = options.add_summary_bullets or options.add_description
    if (has_overview_stage and processing_instructions) or segment_hints is not None:
        import yaml

        result = _attach_late_inputs(
            result,
            processing_instructions=processing_instructions,
            segment_hints=(
                yaml.safe_dump(segment_hints, sort_keys=True) if segment_hints else None
            ),
        )

    if options.add_summary_bullets:
        result = add_transcript_outline(result)

    if options.add_description:
        result = add_transcript_description(result)

    if options.insert_frame_captures:
        from kash.workspaces import current_ws

        # Frames land in the step's sidematter inside the workspace, and the stage will
        # pull the video into the media cache if only the audio was kept. Both go on the
        # workspace volume, and this stage runs after the expensive LLM ones — a run that
        # dies here has already paid for everything above it.
        check_frame_capture_space(current_ws().base_dir)
        result = insert_frame_captures(result)
        result = _thin_frame_captures(result)

    _suggest_segments(result, segment_hints)

    if options.extract_concepts and options.format:
        from deep_transcribe.concept_map import extract_transcript_concepts

        result = extract_transcript_concepts(result, web_search=options.web_search)

    if options.build_index and options.format:
        from deep_transcribe.transcript_index import attach_transcript_index

        result = attach_transcript_index(result)

    if not has_overview_stage:
        set_processing_instructions(result, processing_instructions)

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
            "additional_context, processing_instructions, key_terms, replacements, "
            "speaker_hints, speaker_roster, and extra."
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
    elements: list[str] | None = None,
    report: bool = False,
) -> TranscriptionOutputs:
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
        report: If True, also describe what the run produced, from the final item

    Returns:
        The generated paths, and the report when one was requested
    """
    # Import dynamically for faster startup.
    from kash.config.setup import kash_setup
    from kash.config.unified_live import get_unified_live
    from kash.exec import kash_runtime

    # Set up kash workspace.
    kash_setup(kash_ws_root=ws_root, rich_logging=True)
    ws_path = ws_root / "workspace"

    # Run all actions in the context of this workspace.
    with kash_runtime(ws_path, rerun=rerun) as runtime:
        # Show the user the workspace info.
        runtime.workspace.log_workspace_info()

        with get_unified_live().status("Processing…"):
            item = _prepare_source_item(url)

            # Everything above this line is metadata: kash asks yt-dlp for the title and
            # duration with `download=False`, so nothing large has been written yet and the
            # source length is already known. The fetch below is what fills the disk, and
            # this is the last moment a run can be stopped without having cost anything.
            # Checked against `ws_root`, which holds the media cache as well as the
            # workspace, rather than the boot volume.
            check_download_space(ws_root, source_duration(item))

            # kash's fetch has already written this item to disk, counters included, so
            # stripping in memory is not enough — the stored metadata is what every action
            # hashes. Persist below when anything was removed.
            counters_stripped = strip_volatile_source_fields(item)
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
            if counters_stripped or source_metadata_changed or item.metadata() != old_metadata:
                persist_item_metadata(item, runtime.workspace)

            result_item = transcribe_with_options(
                item,
                options,
                language=language,
                transcription_model=transcription_model,
                diarize_model=diarize_model,
                rerun_processing=rerun_processing,
            )

            transcript_path, html_path = format_results(
                result_item, runtime.workspace.base_dir, no_minify=no_minify, elements=elements
            )
            # Built here, inside the runtime and while the exported item is still in hand,
            # because that item is the only thing that knows what this run produced.
            return TranscriptionOutputs(
                transcript_path,
                html_path,
                report=_build_report(result_item) if report else None,
            )


def _build_report(result_item: Item) -> TranscriptReport:
    """Describe the exported item. Imported lazily to keep a plain run's startup unchanged."""
    from deep_transcribe.transcript_report import build_transcript_report

    return build_transcript_report(result_item)


def _source_aliases(source: str) -> set[str]:
    """Every spelling of a source that could be stored as an item's `url`."""
    locator = _media_source_locator(source)
    return {source, source.rstrip("/"), locator, locator.rstrip("/")}


PIPELINE_STAGE_ORDER = (
    "transcribe",
    "infer_speaker_roster_from_context",
    "correct_speaker_turns",
    "normalize_transcript_fragments",
    "strip_html",
    "break_into_paragraphs",
    "backfill_timestamps",
    "normalize_timestamp_citations",
    "insert_section_headings",
    "research_paras",
    "_attach_late_inputs",
    "add_transcript_outline",
    "add_transcript_description",
    "insert_frame_captures",
    "extract_transcript_concepts",
    "attach_transcript_index",
)
"""
The stages `_process_transcript` applies, in the order it applies them.

Only used to rank stored items by how far down the pipeline each one got, so a re-export
picks the result that reached furthest rather than whichever file was written last. It
mirrors `_process_transcript` and is pinned to it by
`test_pipeline_stage_order_covers_the_stages_the_pipeline_runs`; a stage this tuple does
not know simply ranks below the ones it does, so a new stage degrades the ranking rather
than breaking the flag.
"""


def _stage_rank(history: object) -> int:
    """
    How far down the pipeline the run that produced an item got, from its last operation.

    Preset-agnostic on purpose: `--basic` ends at `transcribe` and `--deep` at
    `attach_transcript_index`, so the rule is "whichever item reached furthest" rather
    than a fixed terminal stage. -1 for an item whose last stage is unrecognized.
    """
    if not isinstance(history, list) or not history:
        return -1
    last = cast("list[object]", history)[-1]
    name = cast("dict[str, object]", last).get("action_name") if isinstance(last, dict) else None
    if not isinstance(name, str) or name not in PIPELINE_STAGE_ORDER:
        return -1
    return PIPELINE_STAGE_ORDER.index(name)


def find_exported_item(workspace: FileStore, source: str) -> StorePath | None:
    """
    The item a finished run for this source last exported, or None if there is not one.

    Found by reading what the workspace already records rather than by a pointer written
    at the end of a run. A pointer would have to live somewhere, and every field of an
    item's metadata is inside the bytes kash hashes for cache identity — which is why
    `strip_volatile_source_fields` exists. Writing the export path onto the source
    resource would therefore change the source's hash after every run and make the next
    run repeat the whole pipeline, paid speech-to-text included. Reading instead costs
    one frontmatter parse per item, needs nothing new on disk, and works on workspaces
    filled in before this flag existed.

    Ranked by how far down the pipeline the item's own last operation reached, then by
    recency. Stage first because an interrupted run leaves half-finished items carrying the
    newest timestamps, and the page should be rebuilt from the result that got furthest
    rather than from whatever was written last. Ranking on the number of history entries
    instead is not enough: a run stopped after concepts and a finished older run both have
    the same count, and recency would then hand the export the item that never got an
    index. The measured workspace holds exactly that pair.
    """
    from frontmatter_format import fmf_read_frontmatter
    from kash.file_storage.store_filenames import folder_for_type, parse_item_filename
    from kash.model import ItemType
    from kash.model.paths_model import StorePath
    from kash.utils.errors import InvalidFilename

    wanted = _source_aliases(source)
    docs_dir = workspace.base_dir / folder_for_type(ItemType.doc)
    best: tuple[int, str, StorePath] | None = None
    for path in sorted(docs_dir.glob("*")):
        if not path.is_file():
            continue
        try:
            _name, item_type, _format, _ext = parse_item_filename(path)
        except InvalidFilename:
            continue
        if item_type is not ItemType.doc:
            continue
        try:
            metadata = fmf_read_frontmatter(path)
        except (OSError, UnicodeDecodeError, ValueError) as error:
            # One unreadable file must not hide the result sitting beside it.
            log.info("Skipping unreadable item while looking for a cached export: %s", error)
            continue
        if not metadata or metadata.get("url") not in wanted:
            continue
        stage = _stage_rank(metadata.get("history"))
        created_at = str(metadata.get("created_at") or "")
        candidate = (stage, created_at, StorePath(path.relative_to(workspace.base_dir)))
        if best is None or candidate[:2] > best[:2]:
            best = candidate
    return best[2] if best else None


def export_only(
    ws_root: Path,
    url: str,
    *,
    no_minify: bool = False,
    elements: list[str] | None = None,
    report: bool = False,
) -> TranscriptionOutputs:
    """
    Rebuild the page from the cached final item, running no stage of the pipeline.

    What a template edit or a different `--elements` selection needs: the analysis is
    already done and correct, and only the rendering changed. Nothing here fetches, asks
    a model, or calls Deepgram — the item is loaded from the workspace and handed to the
    same `format_results` a normal run ends with.

    Raises:
        NoCachedResult: when the workspace holds no finished run for this source.
    """
    from kash.config.setup import kash_setup
    from kash.exec import kash_runtime

    kash_setup(kash_ws_root=ws_root, rich_logging=True)
    ws_path = ws_root / "workspace"

    with kash_runtime(ws_path) as runtime:
        workspace = runtime.workspace
        store_path = find_exported_item(workspace, url)
        if store_path is None:
            raise NoCachedResult(
                f"No cached result for {url} in {workspace.base_dir}. "
                "Run the same command without --export-only first."
            )
        log.info("Re-exporting the cached result at %s", store_path)
        result_item = workspace.load(store_path)
        transcript_path, html_path = format_results(
            result_item, workspace.base_dir, no_minify=no_minify, elements=elements
        )
        return TranscriptionOutputs(
            transcript_path,
            html_path,
            report=_build_report(result_item) if report else None,
        )


PAGE_ELEMENTS = (
    "title",
    "thumbnail",
    "summary",
    "timeline",
    "speakers",
    "outline",
    "concepts",
    "claims",
    "frames",
    "transcript",
)
"""Parts of the exported page that `--elements` can select. Default: all."""


def parse_page_elements(spec: str) -> list[str]:
    """Parse and validate a comma-separated `--elements` value."""
    elements = [name.strip() for name in spec.split(",") if name.strip()]
    unknown = [name for name in elements if name not in PAGE_ELEMENTS]
    if unknown:
        raise ValueError(
            f"Unknown element(s) {', '.join(unknown)}. Valid elements: {', '.join(PAGE_ELEMENTS)}"
        )
    if not elements:
        raise ValueError(f"--elements needs at least one of: {', '.join(PAGE_ELEMENTS)}")
    return elements


def inject_page_elements(html: str, elements: list[str] | None) -> str:
    """
    Inject the element selection into the exported page as configuration.

    The client reads `window.DT_ELEMENTS`, skips excluded panels, and hides
    excluded stored content. No selection means the full page.
    """
    if elements is None or set(elements) == set(PAGE_ELEMENTS):
        return html
    config = f"<script>window.DT_ELEMENTS = {json.dumps(list(elements))};</script>"
    marker = "</body>"
    if marker not in html:
        return html + config
    return html.replace(marker, f"{config}\n{marker}", 1)


# Matches a sidematter assets directory prefix in an image path, e.g.
# `watch_step13_insert_frame_captures_1.doc.assets/frame_0000.jpg`.
_ASSETS_REF = re.compile(r"(?P<prefix>[A-Za-z0-9][A-Za-z0-9._-]*\.assets)/")


def relocate_referenced_assets(html_path: Path, source_dir: Path) -> bool:
    """
    Copy the assets an exported page references into the page's own sidematter.

    Frame captures are written into the sidematter of the `insert_frame_captures` step,
    and every stage deriving from it carries the body forward without the assets. Those
    references resolve only while the file sits beside the step that owns them, so an
    export written to a different directory has every image broken. Copy what the page
    actually references and repoint the paths at the copy.

    Operates on the written file rather than the item, because the item that reaches
    disk last (after minification) is external and will not be rewritten by a save.

    Returns True if the page was rewritten.
    """
    from sidematter_format import Sidematter
    from strif import atomic_output_file

    text = html_path.read_text()
    own_assets = Sidematter(html_path).assets_dir
    prefixes = {m.group("prefix") for m in _ASSETS_REF.finditer(text)} - {own_assets.name}
    if not prefixes:
        return False

    copied = 0
    for prefix in sorted(prefixes):
        src_dir = source_dir / prefix
        if not src_dir.is_dir():
            log.warning("Referenced assets are missing, images will break: %s", src_dir)
            continue
        copied += len(Sidematter(html_path).copy_assets_from(src_dir))
        text = text.replace(f"{prefix}/", f"{own_assets.name}/")

    if not copied:
        return False

    log.info("Relocated %s referenced assets into %s", copied, own_assets)
    with atomic_output_file(html_path) as temp_path:
        temp_path.write_text(text)
    return True


SUGGESTED_SEGMENTS_NAME = "segments.suggested.yml"
"""Where a detected preview clip is written for the user to review."""


def _hints_in_effect(item: Item, existing_hints: object) -> SegmentHints:
    """
    The hints governing this run, from wherever they are being carried.

    The argument is what the caller lifted off the source item to keep it out of the
    cached stages; the item's own metadata is where `_attach_late_inputs` puts the same
    hints back, below the cache boundary. Both are read so the answer does not depend on
    which of the two a caller happens to hold.
    """
    from deep_transcribe.segment_hints import SegmentHint, SegmentHints, parse_hints
    from deep_transcribe.transcription_metadata import get_segment_hints

    segments: list[SegmentHint] = []
    for raw in (existing_hints, get_segment_hints(item)):
        if raw is None:
            continue
        try:
            segments.extend(parse_hints(raw).segments)
        except ValueError as error:
            log.warning(
                "Cannot read the segment hints in effect, checking against the rest: %s", error
            )
    return SegmentHints(segments)


def _suggest_segments(item: Item, existing_hints: object) -> None:
    """
    Draft a hints file when the opening turns out to be a highlight reel.

    Detection proposes; it never applies. The user asked for a loop where the output is
    looked at and the hints revised, so what a detector is good for is saving the first
    edit — writing down a range someone would otherwise have to find by scrubbing.

    A detection the hints in effect already account for is not worth writing down: asking
    someone to adopt the segment they just adopted teaches them to stop reading these
    messages. So the clip is checked against those hints first, and the file is only ever
    written when it is absent, since overwriting what someone is iterating on is the one
    thing this must not do.
    """
    if not item.body:
        return
    from kash.workspaces.workspaces import current_ws

    from deep_transcribe.preview_detection import detect_preview_clip
    from deep_transcribe.segment_hints import (
        SegmentHint,
        SegmentHints,
        SegmentPurpose,
        format_span_outward,
        write_hints,
    )
    from deep_transcribe.transcript_index import scan_raw_units

    try:
        clip = detect_preview_clip(scan_raw_units(item.body))
    except Exception as error:
        log.warning("Preview detection failed, continuing without a suggestion: %s", error)
        return
    if clip is None:
        return

    marked = _hints_in_effect(item, existing_hints).covering(clip.start, clip.end)
    if marked:
        log.info(
            "The opening looks like a highlight reel (%s), and the segment hints in effect "
            "already mark it as %s (%s). Nothing to suggest.",
            format_span_outward(clip.start, clip.end),
            marked.purpose.value,
            format_span_outward(marked.start, marked.end),
        )
        return

    path = current_ws().base_dir / SUGGESTED_SEGMENTS_NAME
    if path.exists():
        return
    write_hints(
        path,
        SegmentHints(
            [
                SegmentHint(
                    start=clip.start,
                    end=clip.end,
                    purpose=SegmentPurpose.teaser,
                    note=(
                        f"{clip.units} paragraphs, {clip.echoed_fraction * 100:.0f}% of them "
                        "found again later in the recording"
                    ),
                )
            ]
        ),
        title=item.title,
    )
    from deep_transcribe.segment_hints import format_time

    log.warning(
        "The opening looks like a highlight reel (%s to %s). Suggested hints written to %s — "
        "review it and rerun with --segments to leave it out of the analysis.",
        format_time(clip.start),
        format_time(clip.end),
        path,
    )


def _thin_frame_captures(item: Item) -> Item:
    """
    Cap frame density on long media, editing in place so no cache entry is invalidated.

    `insert_frame_captures` has already written the files and the tags; this only decides
    which of them survive. Doing it as a mutation of the same item rather than a derived
    one keeps the frame capture step's own cache intact, so a rerun does not pay for the
    captures again — and it is what makes the saving real, since a derived copy would
    leave all the original images on disk.

    The dropped images are deleted, so that cache entry can no longer produce the full
    set; recovering them means rerunning the capture.
    """
    from sidematter_format import Sidematter

    from deep_transcribe.frame_density import thin_frame_captures

    if not item.body or not item.store_path:
        return item
    from kash.workspaces.workspaces import current_ws

    assets_dir = Sidematter(current_ws().base_dir / item.store_path).assets_dir
    body, removed = thin_frame_captures(item.body, assets_dir)
    if not removed:
        return item
    item.body = body
    # overwrite=True matters: the thinned frames have already been deleted from disk, so
    # a stored document still listing them would point at files that are gone.
    current_ws().save(item, overwrite=True)
    return item


def format_results(
    result_item: Item,
    base_dir: Path,
    no_minify: bool = False,
    elements: list[str] | None = None,
) -> tuple[Path, Path]:
    """
    Format the results of a transcription into HTML and ensure proper file paths.

    Args:
        result_item: The transcription result item
        base_dir: Base directory for output files
        no_minify: If True, skip HTML minification
        elements: Page parts to include (see PAGE_ELEMENTS); None means all

    Returns:
        Tuple of (transcript_path, html_path) for the generated files
    """
    # Import dynamically for faster startup.
    from kash.actions.core.minify_html import minify_html
    from kash.model import Format, ItemType
    from kash.web_gen.template_render import additional_template_dirs
    from kash.web_gen.webpage_render import render_item_as_html
    from kash.workspaces.workspaces import current_ws

    raw_html_item = result_item.derived_copy(
        type=ItemType.export,
        format=Format.html,
    )
    templates_dir = Path(__file__).parent / "resources" / "templates"
    with additional_template_dirs(templates_dir):
        raw_html_item = render_item_as_html(
            result_item,
            raw_html_item,
            add_title_h1=True,
            template_filename="deep_transcribe_webpage.html.jinja",
        )
    assert raw_html_item.body
    raw_html_item.body = inject_page_elements(raw_html_item.body, elements)
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

    relocate_referenced_assets(html_path, transcript_path.parent)

    return transcript_path, html_path


## Tests


def test_parse_page_elements_validates_names() -> None:
    assert parse_page_elements("summary, timeline") == ["summary", "timeline"]

    import pytest

    with pytest.raises(ValueError, match="Unknown element"):
        parse_page_elements("summary,bogus")
    with pytest.raises(ValueError, match="at least one"):
        parse_page_elements(" , ")


def test_inject_page_elements_only_when_subset() -> None:
    html = "<html><body><p>x</p></body></html>"

    assert inject_page_elements(html, None) == html
    assert inject_page_elements(html, list(PAGE_ELEMENTS)) == html

    injected = inject_page_elements(html, ["summary", "timeline"])
    assert 'window.DT_ELEMENTS = ["summary", "timeline"];' in injected
    assert injected.index("DT_ELEMENTS") < injected.index("</body>")


def test_format_results_relocates_assets_through_minification() -> None:
    """
    Minification derives yet another item, so the assets have to follow the item that is
    actually written, not the one that was rendered.
    """
    from tempfile import TemporaryDirectory

    from kash.exec import kash_runtime
    from kash.model import Format, ItemType
    from kash.workspaces import current_ws
    from sidematter_format import Sidematter
    from strif import atomic_output_file

    with TemporaryDirectory() as temp_dir:
        with kash_runtime(Path(temp_dir) / "workspace"):
            ws = current_ws()
            frames_item = Item(
                type=ItemType.doc,
                format=Format.md_html,
                title="Minified transcript with frames",
            )
            frames_path = ws.assign_store_path(frames_item)
            frames_assets = Sidematter(frames_path).assets_dir
            frames_item.body = f'<img src="{frames_assets.name}/frame.jpg" alt="Frame">'
            ws.save(frames_item)
            with atomic_output_file(frames_assets / "frame.jpg", make_parents=True) as tmp:
                tmp.write_bytes(b"frame")

            result_item = frames_item.derived_copy(type=ItemType.doc)
            ws.save(result_item)

            _, html_path = format_results(result_item, ws.base_dir)

            html_assets = Sidematter(html_path).assets_dir
            html_text = html_path.read_text()
            assert f"{html_assets.name}/frame.jpg" in html_text
            assert (html_assets / "frame.jpg").read_bytes() == b"frame"
            assert frames_assets.name not in html_text


def test_exact_roster_skips_prose_inference() -> None:
    from unittest.mock import patch

    from kash.model import ItemType

    item = Item(
        type=ItemType.doc,
        body="Transcript.",
        additional_context="There are two speakers.",
        extra={"transcription": {"speaker_roster": ["Host", "Guest"]}},
    )

    with (
        patch("deep_transcribe.speaker_correction.infer_speaker_roster_from_context") as infer,
        patch(
            "deep_transcribe.speaker_correction.correct_speaker_turns",
            return_value=item,
        ) as correct,
        patch("kash.kits.media.actions.transcribe.identify_speakers.identify_speakers") as identify,
    ):
        result = _identify_transcript_speakers(item)

    assert result is item
    infer.assert_not_called()
    correct.assert_called_once_with(item)
    identify.assert_not_called()


def test_prose_roster_is_inferred_before_boundary_correction() -> None:
    from unittest.mock import patch

    from kash.model import ItemType

    item = Item(
        type=ItemType.doc,
        body="Transcript.",
        additional_context="There are two speakers: the host and guest.",
    )
    inferred = item.new_copy_with(extra={"transcription": {"speaker_roster": ["Host", "Guest"]}})

    with (
        patch(
            "deep_transcribe.speaker_correction.infer_speaker_roster_from_context",
            return_value=inferred,
        ) as infer,
        patch(
            "deep_transcribe.speaker_correction.correct_speaker_turns",
            return_value=inferred,
        ) as correct,
        patch("kash.kits.media.actions.transcribe.identify_speakers.identify_speakers") as identify,
    ):
        result = _identify_transcript_speakers(item)

    assert result is inferred
    infer.assert_called_once_with(item, web_search=False)
    correct.assert_called_once_with(inferred)
    identify.assert_not_called()


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
            # Frames land in the sidematter of the frame-capture step, and later stages
            # derive new docs from it without carrying the assets. Reproduce that shape:
            # the item being exported must not own the assets its body points at.
            frames_item = Item(
                type=ItemType.doc,
                format=Format.md_html,
                title="Transcript with frames",
            )
            frames_path = ws.assign_store_path(frames_item)
            frames_assets = Sidematter(frames_path).assets_dir
            frames_item.body = f'<img src="{frames_assets.name}/frame.jpg" alt="Frame">'
            ws.save(frames_item)

            with atomic_output_file(frames_assets / "frame.jpg", make_parents=True) as tmp:
                tmp.write_bytes(b"frame")

            result_item = frames_item.derived_copy(type=ItemType.doc)
            source_path = ws.assign_store_path(result_item)
            ws.save(result_item)
            assert not Sidematter(source_path).assets_dir.exists()

            transcript_path, html_path = format_results(
                result_item,
                ws.base_dir,
                no_minify=True,
            )

            html_assets = Sidematter(html_path).assets_dir
            html_text = html_path.read_text()
            assert transcript_path == source_path
            assert f"{html_assets.name}/frame.jpg" in html_text
            assert (html_assets / "frame.jpg").read_bytes() == b"frame"
            # Nothing may still point at the upstream step's directory, or the export
            # only works while it sits beside that step.
            assert frames_assets.name not in html_text
            assert "Transcribed by github.com/jlevy/deep-transcribe" in html_text
            assert "font-family: var(--font-sans) !important" in html_text
            assert html_text.count("font-size: 9pt") == 3
            # The footer note and the page number share a size and alignment so they
            # print on one baseline.
            assert html_text.count("vertical-align: bottom") == 2
            assert "max-width: 45%" in html_text
            assert "color: var(--color-tertiary) !important" in html_text
            assert ".long-text p:has(> .frame-capture)" in html_text
            assert "break-inside: avoid" in html_text
            assert ".theme-toggle" in html_text
            assert ".timestamp-link:hover" in html_text
            assert ".timestamp-link a" in html_text
            # Screen and print timestamps share the light-gray treatment.
            assert "color: var(--color-secondary) !important" not in html_text
            assert "display: none !important" in html_text
            assert 'id="yt-popover"' in html_text
