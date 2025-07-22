from __future__ import annotations

from dataclasses import dataclass


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
            research_paras=False,  # Exclude research for annotated
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
        """
        Parse comma-separated option names and return a TranscribeOptions instance.
        """
        options = cls()
        if not with_flags.strip():
            return options

        # Split on comma and strip whitespace
        flag_names = [flag.strip() for flag in with_flags.split(",")]

        for flag_name in flag_names:
            if not flag_name:
                continue
            if hasattr(options, flag_name):
                setattr(options, flag_name, True)
            else:
                valid_options = [
                    field for field in options.__dataclass_fields__ if not field.startswith("_")
                ]
                raise ValueError(
                    f"Unknown option '{flag_name}'. Valid options: {', '.join(valid_options)}"
                )

        return options

    def merge_with(self, other: TranscribeOptions) -> TranscribeOptions:
        """
        Merge this options instance with another, using OR logic for boolean flags.
        """
        return TranscribeOptions(
            identify_speakers=self.identify_speakers or other.identify_speakers,
            format=self.format or other.format,
            insert_section_headings=self.insert_section_headings or other.insert_section_headings,
            research_paras=self.research_paras or other.research_paras,
            add_summary_bullets=self.add_summary_bullets or other.add_summary_bullets,
            add_description=self.add_description or other.add_description,
            insert_frame_captures=self.insert_frame_captures or other.insert_frame_captures,
        )

    def get_enabled_options(self) -> list[str]:
        """
        Get list of enabled option names from this TranscribeOptions instance.
        """
        enabled: list[str] = []
        for field_name in self.__dataclass_fields__:
            if getattr(self, field_name):
                enabled.append(field_name)
        return enabled
