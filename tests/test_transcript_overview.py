from kash.model import Item, ItemType

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
