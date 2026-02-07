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
       - HTML stripping, paragraph breaking, timestamp backfilling
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
    """Add a bulleted summary of the content at the top."""

    add_description: bool = False
    """Add a description at the top of the transcript."""

    insert_frame_captures: bool = False
    """Insert frame captures from video (for video content)."""

    @classmethod
    def basic(cls) -> TranscribeOptions:
        return cls()

    @classmethod
    def formatted(cls) -> TranscribeOptions:
        return cls(format=True, identify_speakers=True)

    @classmethod
    def annotated(cls) -> TranscribeOptions:
        return cls(
            format=True,
            identify_speakers=True,
            insert_section_headings=True,
            research_paras=False,
            add_summary_bullets=True,
            add_description=True,
            insert_frame_captures=True,
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
        )

    @classmethod
    def from_with_flags(cls, with_flags: str) -> TranscribeOptions:
        """Parse comma-separated option names and return a TranscribeOptions instance."""
        options = cls()
        if not with_flags.strip():
            return options

        valid_fields = {f.name for f in fields(options) if f.type == "bool"}
        flag_names = [flag.strip() for flag in with_flags.split(",") if flag.strip()]

        for flag_name in flag_names:
            if flag_name not in valid_fields:
                raise ValueError(
                    f"Unknown option '{flag_name}'. Valid options: {', '.join(sorted(valid_fields))}"
                )
            setattr(options, flag_name, True)

        return options

    def merge_with(self, other: TranscribeOptions) -> TranscribeOptions:
        """Merge with another instance, using OR logic for boolean flags."""
        return TranscribeOptions(
            **{f.name: getattr(self, f.name) or getattr(other, f.name) for f in fields(self)}
        )

    def get_enabled_options(self) -> list[str]:
        """Get list of enabled option names."""
        return [f.name for f in fields(self) if getattr(self, f.name)]
