from pathlib import Path
from unittest.mock import patch

from kash.model import Format, Item, ItemType
from kash.utils.common.url import Url

from deep_transcribe.transcript_overview import (
    CHUNK_SUMMARY_PROMPT,
    DESCRIPTION_PROMPT,
    OUTLINE_PROMPT,
    SYNOPSIS_REDUCE_PROMPT,
    add_transcript_description,
    add_transcript_outline,
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
    assert "outline or another stage" in DESCRIPTION_PROMPT
    assert "existing section headings" in OUTLINE_PROMPT
    assert "two to four sub-bullets" in OUTLINE_PROMPT
    assert "synopsis or another stage" in OUTLINE_PROMPT

    for overview_action in (add_transcript_outline, add_transcript_description):
        action_class = getattr(overview_action, "__action_class__")  # noqa: B009
        action = action_class.create(None)
        assert action.output_type is ItemType.doc
        assert action.output_format is Format.md_html


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


def _long_body(sections: int, minutes_apart: int) -> str:
    return "".join(
        f"## Section {i}\n\n**Alice:** Point {i}.\n"
        '<span class="citation timestamp-link" data-src="r.yml" '
        f'data-timestamp="{i * minutes_apart * 60}.00"><a href="https://x">t</a></span>\n\n'
        for i in range(sections)
    )


def _runtime(tmp_path: Path):
    """The actions resolve source metadata through a workspace, so give them an empty one."""
    from kash.exec import kash_runtime

    return kash_runtime(tmp_path / "workspace")


def test_outline_runs_per_chunk_and_never_sends_the_whole_document(tmp_path: Path) -> None:
    body = _long_body(9, 10)  # 80 minutes
    item = Item(type=ItemType.doc, format=Format.md_html, body=body)
    sent: list[str] = []

    def fake_transform(prepared: Item, **_kwargs: object) -> Item:
        assert prepared.body
        sent.append(prepared.body)
        return prepared.new_copy_with(body=f"- **Chunk {len(sent)}**\n  - A point")

    with (
        _runtime(tmp_path),
        patch("deep_transcribe.transcript_overview.llm_transform_item", fake_transform),
    ):
        outlined = add_transcript_outline(item)

    assert len(sent) == 3
    assert all("Point 0." not in text for text in sent[1:])
    # Every call is a fraction of the document, which is the whole point.
    assert all(len(text) < len(body) for text in sent)
    assert outlined.body
    for i in (1, 2, 3):
        assert f"**Chunk {i}**" in outlined.body


def test_synopsis_reduces_chunk_summaries_for_long_media(tmp_path: Path) -> None:
    item = Item(type=ItemType.doc, format=Format.md_html, body=_long_body(9, 10))
    prompts: list[str] = []

    def fake_complete(_model: object, prompt: str, body: str | None) -> str:
        prompts.append(prompt)
        if "Summaries, in order" in prompt:
            return "Reduced synopsis."
        return f"Summary of {(body or '')[:1]}"

    with (
        _runtime(tmp_path),
        patch("deep_transcribe.transcript_overview._complete", fake_complete),
    ):
        described = add_transcript_description(item)

    assert len(prompts) == 4  # three chunk summaries, then one reduce
    assert prompts.count(SYNOPSIS_REDUCE_PROMPT) == 1
    assert prompts[:3] == [CHUNK_SUMMARY_PROMPT] * 3
    assert described.body and "Reduced synopsis." in described.body


def test_short_media_still_takes_the_single_call_path(tmp_path: Path) -> None:
    item = Item(type=ItemType.doc, format=Format.md_html, body=_long_body(3, 5))  # 10 min
    calls: list[Item] = []

    def fake_transform(prepared: Item, **_kwargs: object) -> Item:
        calls.append(prepared)
        return prepared.new_copy_with(body="A synopsis.")

    with (
        _runtime(tmp_path),
        patch("deep_transcribe.transcript_overview.llm_transform_item", fake_transform),
    ):
        described = add_transcript_description(item)

    assert len(calls) == 1
    assert described.body and "A synopsis." in described.body
