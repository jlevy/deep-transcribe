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
    """Add a bulleted summary at the end."""

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


## Tests


def test_transcribe_options_parsing():
    """Test that TranscribeOptions parses comma-separated flags correctly."""
    # Test basic parsing
    options = TranscribeOptions.from_with_flags("format,insert_section_headings")
    assert options.format
    assert options.insert_section_headings
    assert not options.research_paras

    # Test empty string
    options = TranscribeOptions.from_with_flags("")
    assert not options.format

    # Test whitespace handling
    options = TranscribeOptions.from_with_flags(" format , insert_section_headings ")
    assert options.format
    assert options.insert_section_headings

    # Test presets
    basic = TranscribeOptions.basic()
    assert not basic.format

    formatted = TranscribeOptions.formatted()
    assert formatted.format
    assert formatted.identify_speakers

    annotated = TranscribeOptions.annotated()
    assert annotated.format
    assert annotated.identify_speakers
    assert annotated.insert_section_headings
    assert not annotated.research_paras  # Annotated excludes research
    assert annotated.add_summary_bullets

    deep = TranscribeOptions.deep()
    assert deep.format
    assert deep.identify_speakers
    assert deep.insert_section_headings
    assert deep.research_paras  # Deep includes research
    assert deep.add_summary_bullets

    # Test merge
    merged = basic.merge_with(formatted)
    assert merged.format
    assert merged.identify_speakers

    print("All tests passed!")


if __name__ == "__main__":
    test_transcribe_options_parsing()
