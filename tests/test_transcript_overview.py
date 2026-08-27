from kash.model import Item, ItemType
from kash.utils.common.url import Url

from deep_transcribe.transcript_overview import (
    DESCRIPTION_PROMPT,
    OUTLINE_PROMPT,
    normalize_transcript_outline,
    prepare_transcript_for_model,
    wrap_transcript_outline,
)


def test_processing_instructions_are_separate_from_transcript_context() -> None:
    item = Item(
        type=ItemType.doc,
        body="Transcript body.",
        extra={
            "transcription": {
                "processing_instructions": "Emphasize the decisions and open questions."
            }
        },
    )

    prepared = prepare_transcript_for_model(item)

    assert item.body == "Transcript body."
    assert prepared.body is not None
    assert "<processing_instructions>" in prepared.body
    assert "Emphasize the decisions and open questions." in prepared.body
    assert "<transcript>\nTranscript body.\n</transcript>" in prepared.body


def test_overview_model_receives_bounded_source_metadata() -> None:
    item = Item(
        type=ItemType.doc,
        body="Transcript body.",
        title="Source title",
        url=Url("https://example.test/watch"),
        description="Source description.",
        additional_context="The user supplied the complete speaker roster.",
        extra={"upload_date": "2026-08-26"},
    )

    prepared = prepare_transcript_for_model(item)

    assert prepared.title is None
    assert prepared.description is None
    assert prepared.additional_context is not None
    assert "Source title: Source title" in prepared.additional_context
    assert "Source publication date: 2026-08-26" in prepared.additional_context
    assert "Canonical source URL: https://example.test/watch" in prepared.additional_context
    assert "User-provided context: The user supplied" in prepared.additional_context


def test_transcript_overview_is_brief_visible_and_section_aligned() -> None:
    item = Item(type=ItemType.doc, body="Transcript body.")

    outlined = wrap_transcript_outline(item, "- **Opening**\n  - Key point")

    assert outlined.body is not None
    assert "<details" not in outlined.body
    assert 'class="transcript-outline"' in outlined.body
    assert "font-family: var(--font-sans)" in outlined.body
    assert outlined.body.index("Outline") < outlined.body.index("Transcript body.")
    assert "two short paragraphs" in DESCRIPTION_PROMPT
    assert "existing section headings" in OUTLINE_PROMPT
    assert "two to four sub-bullets" in OUTLINE_PROMPT


def test_outline_discards_model_preamble_before_the_first_section() -> None:
    response = """Repeated title

Repeated synopsis paragraph.

- **Opening**
  - Key point
- **Discussion**
  - Suggestion
"""

    assert normalize_transcript_outline(response) == (
        "- **Opening**\n  - Key point\n- **Discussion**\n  - Suggestion"
    )
