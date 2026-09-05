from __future__ import annotations

from dataclasses import dataclass, fields


@dataclass
class TranscribeOptions:
    """
    Options for transcription processing pipeline.

    Processing steps are applied in order:
    1. Basic transcription (always performed)
    2. Formatting pipeline (if format=True):
       - Speaker identification (if identify_speakers=True)
       - HTML stripping, paragraph breaking, back-channel folding (unless
         keep_back_channel=True), timestamp backfilling
    3. Annotation steps (applied individually if enabled):
       - Section headings
       - Paragraph research
       - Summary bullets
       - Description
       - Frame captures
    """

    identify_speakers: bool = False
    """Identify different speakers in the audio/video."""

    format: bool = False
    """Apply formatting pipeline: speakers, paragraphs, timestamps."""

    insert_section_headings: bool = False
    """Add section headings to break up content."""

    research_paras: bool = False
    """Add research annotations to paragraphs."""

    add_summary_bullets: bool = False
    """Add a concise, section-aligned outline at the top."""

    add_description: bool = False
    """Add a brief paragraph-broken synopsis at the top."""

    insert_frame_captures: bool = False
    """Insert frame captures from video (for video content)."""

    build_index: bool = False
    """Embed the JSON transcript index used by the timeline and analytics views."""

    extract_concepts: bool = False
    """Extract a concept map from the transcript (LLM stage)."""

    web_search: bool = False
    """Let the speaker roster step corroborate facts with web search."""

    keep_back_channel: bool = False
    """Leave one-word acknowledgement turns as their own paragraphs instead of folding them."""
    no_chapters: bool = False
    """
    Ignore the publisher's chapters instead of using them as the section skeleton.

    Spelled as an opt-out rather than a default-on `use_chapters` because of how these
    flags compose: `merge_with` ORs every field, so one that starts True can never be
    turned off by a merge, and `get_enabled_options` reports whatever is truthy, which
    would list a default-on stage in every preset's help — `--basic` included, which does
    no formatting at all.
    """

    @classmethod
    def basic(cls) -> TranscribeOptions:
        return cls()

    @classmethod
    def formatted(cls) -> TranscribeOptions:
        return cls(format=True, identify_speakers=True, build_index=True)

    @classmethod
    def annotated(cls) -> TranscribeOptions:
        return cls(
            format=True,
            identify_speakers=True,
            insert_section_headings=True,
            research_paras=False,  # Exclude research for annotated
            add_summary_bullets=True,
            add_description=True,
            insert_frame_captures=True,
            build_index=True,
        )

    @classmethod
    def deep(cls) -> TranscribeOptions:
        return cls(
            format=True,
            identify_speakers=True,
            insert_section_headings=True,
            research_paras=True,  # Include research for deep
            add_summary_bullets=True,
            add_description=True,
            insert_frame_captures=True,
            build_index=True,
            extract_concepts=True,
        )

    @classmethod
    def from_with_flags(cls, with_flags: str) -> TranscribeOptions:
        """Parse comma-separated option names and return a `TranscribeOptions` instance."""
        options = cls()
        if not with_flags.strip():
            return options

        valid_fields = {field.name for field in fields(options)}
        flag_names = [flag.strip() for flag in with_flags.split(",") if flag.strip()]

        for flag_name in flag_names:
            if flag_name not in valid_fields:
                raise ValueError(
                    f"Unknown option '{flag_name}'. Valid options: {', '.join(sorted(valid_fields))}"
                )
            setattr(options, flag_name, True)

        return options

    def merge_with(self, other: TranscribeOptions) -> TranscribeOptions:
        """Merge with another instance, using OR logic for all flags."""
        return TranscribeOptions(
            **{
                field.name: getattr(self, field.name) or getattr(other, field.name)
                for field in fields(self)
            }
        )

    def get_enabled_options(self) -> list[str]:
        """Get enabled option names."""
        return [field.name for field in fields(self) if getattr(self, field.name)]


PIPELINE_STAGE_ORDER = (
    "transcribe",
    "apply_transcript_replacements",
    "infer_speaker_roster_from_context",
    "correct_speaker_turns",
    "normalize_transcript_fragments",
    "strip_html",
    "break_into_paragraphs",
    "fold_back_channel_turns",
    "backfill_timestamps",
    "normalize_timestamp_citations",
    "insert_chapter_headings",
    "insert_section_headings",
    "demote_model_headings",
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

Two things read it. A re-export ranks stored items by how far down the pipeline each one
got, so it picks the result that reached furthest rather than whichever file was written
last. And `--rerun-from` validates its argument against it and lists the names in
`--help`, which is why the tuple lives in this kash-free module: building the parser must
not pay for importing kash.

It mirrors `_process_transcript` and is pinned to it by
`test_pipeline_stage_order_covers_the_stages_the_pipeline_runs`; a stage this tuple does
not know simply ranks below the ones it does, so a new stage degrades the ranking rather
than breaking either flag.
"""
