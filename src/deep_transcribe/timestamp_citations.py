from __future__ import annotations

import re

from kash.exec import kash_action
from kash.exec.preconditions import has_simple_text_body
from kash.model import Format, Item, ItemType
from kash.utils.errors import InvalidInput

_TIMESTAMP_ICON_PREFIX_PATTERN = re.compile(
    r'(?P<opening><span\b(?=[^>]*\bclass="[^"]*\btimestamp-link\b)[^>]*>)'
    r'(?:(?:<span\b(?=[^>]*\bclass="[^"]*\btimestamp-icon\b)[^>]*>).*?</span>|⏱️)+',
    re.DOTALL,
)
_LOCAL_FILE_TIMESTAMP_LINK_PATTERN = re.compile(
    r'<a\b[^>]*\bhref="file://[^"]*"[^>]*>(?P<label>[^<]*)</a>(?=&nbsp;</span>)'
)


@kash_action(precondition=has_simple_text_body)
def normalize_timestamp_citations(item: Item) -> Item:
    """Keep local timestamp citations useful without exposing unusable file links."""
    if not item.body:
        raise InvalidInput(f"Item must have a body: {item}")

    body = _TIMESTAMP_ICON_PREFIX_PATTERN.sub(r"\g<opening>", item.body)
    body = _LOCAL_FILE_TIMESTAMP_LINK_PATTERN.sub(r"\g<label>", body)
    return item.derived_copy(body=body)


## Tests


def test_normalize_timestamp_citations_keeps_only_seekable_links() -> None:
    from inspect import unwrap

    local_citation = (
        '<span class="citation timestamp-link" data-timestamp="123.00">'
        '<span class="timestamp-icon" aria-hidden="true">⏱️</span>'
        '<a href="file:///private/video.mp4">02:03</a>&nbsp;</span>'
    )
    web_citation = (
        '<span class="citation timestamp-link" data-timestamp="456.00">⏱️'
        '<a href="https://www.youtube.com/watch?v=abcdefghijk&amp;t=456s">'
        "07:36</a>&nbsp;</span>"
    )
    item = Item(
        type=ItemType.doc,
        format=Format.md_html,
        body=f"Local {local_citation}\n\nWeb {web_citation}",
    )

    result = unwrap(normalize_timestamp_citations)(item)

    assert result.body is not None
    assert "⏱️" not in result.body
    assert "file://" not in result.body
    assert ">02:03&nbsp;</span>" in result.body
    assert '<a href="https://www.youtube.com/' in result.body
