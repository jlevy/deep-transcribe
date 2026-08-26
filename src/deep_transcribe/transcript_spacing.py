from __future__ import annotations

import re

from kash.exec import kash_action
from kash.exec.preconditions import has_html_body
from kash.model import Format, Item, ItemType
from kash.utils.errors import InvalidInput

_ADJACENT_TIMESTAMP_SPAN_PATTERN = re.compile(
    r"(</span>)[ \t\r\n]+(?=<span\b(?=[^>]*\bdata-timestamp=))"
)


@kash_action(precondition=has_html_body)
def normalize_transcript_fragments(item: Item) -> Item:
    """Remove false paragraph boundaries between timestamp spans in one speaker turn."""
    if not item.body:
        raise InvalidInput(f"Item must have a body: {item}")

    body = _ADJACENT_TIMESTAMP_SPAN_PATTERN.sub(r"\1 ", item.body)
    return item.derived_copy(body=body)


## Tests


def test_normalize_transcript_fragments_preserves_speaker_turns() -> None:
    from inspect import unwrap

    first_label = '<span class="speaker-label" data-speaker-id="0">SPEAKER 0:</span>'
    second_label = '<span class="speaker-label" data-speaker-id="1">SPEAKER 1:</span>'
    first_sentence = '<span data-timestamp="1.0">This</span>'
    second_sentence = '<span data-timestamp="2.0">continues.</span>'
    reply = '<span data-timestamp="3.0">Reply.</span>'
    item = Item(
        type=ItemType.doc,
        format=Format.html,
        body=(f"{first_label}\n{first_sentence}\n\n\n{second_sentence}\n\n{second_label}\n{reply}"),
    )

    result = unwrap(normalize_transcript_fragments)(item)

    assert result.body == (
        f"{first_label} {first_sentence} {second_sentence}\n\n{second_label} {reply}"
    )
