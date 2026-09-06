from __future__ import annotations

import re
from collections.abc import Mapping

from kash.config.logger import get_logger
from kash.exec import kash_action
from kash.exec.preconditions import has_body
from kash.model import Item
from kash.utils.errors import InvalidInput

from deep_transcribe.transcription_metadata import get_replacements

log = get_logger(__name__)

_MARKUP_PATTERN = re.compile(r"<!--.*?-->|<[^>]*>", re.DOTALL)
"""
HTML comments and tags, so a replacement can only ever reach a text node.

The transcript at this point is HTML whose every sentence is wrapped in a timestamp span,
and a speaker label carries the speaker's name in an attribute. A plain string replacement
over the whole body would rewrite `data-speaker-id` values and any name that appears in an
attribute, which is how a "harmless" find-and-replace corrupts the citation structure the
timeline and the index are built from.
"""


def _cased_like(matched: str, wrong: str, right: str) -> str:
    """
    Spell the correction the way the occurrence was spelled.

    An exact match of the mapping's own key is answered verbatim, which is what makes a
    mapping like `omakub: Omakub` able to fix capitalization at all. Otherwise the case of
    the occurrence wins: a lowercase mishearing stays lowercase, a shouted one stays
    shouted, and a capitalized one keeps the correction's own internal capitals.
    """
    if matched == wrong:
        return right
    if matched.islower():
        return right.lower()
    if matched.isupper() and len(matched) > 1:
        return right.upper()
    if matched[:1].isupper() and matched[1:].islower():
        return right[:1].upper() + right[1:]
    return right


def apply_replacements(text: str, replacements: Mapping[str, str]) -> tuple[str, dict[str, int]]:
    """
    Replace whole words in text nodes only, and report how often each one was applied.

    Whole-word so `Omachi` never rewrites the middle of another word; case-preserving so
    the correction reads as the speaker's sentence rather than a stamped-in token. A
    trailing plural `s` and any possessive follow the word: `Omachis` becomes `Omarchys`
    and `Omachi's` becomes `Omarchy's`.

    One pass over the text, not one pass per entry, so a mapping cannot cascade: with
    `{A: B, B: C}` an `A` becomes `B` and stays `B`.
    """
    counts = dict.fromkeys(replacements, 0)
    if not replacements:
        return text, counts

    lookup = {wrong.casefold(): wrong for wrong in replacements}
    # Longest first so `Omachi Linux` wins over `Omachi` when a mapping holds both.
    alternation = "|".join(
        re.escape(wrong) for wrong in sorted(replacements, key=len, reverse=True)
    )
    word_pattern = re.compile(rf"\b(?P<word>{alternation})s?\b", re.IGNORECASE)

    def substitute(match: re.Match[str]) -> str:
        base = match.group("word")
        wrong = lookup[base.casefold()]
        counts[wrong] += 1
        suffix = match.group(0)[len(base) :]
        return _cased_like(base, wrong, replacements[wrong]) + suffix

    parts: list[str] = []
    position = 0
    for markup in _MARKUP_PATTERN.finditer(text):
        parts.append(word_pattern.sub(substitute, text[position : markup.start()]))
        parts.append(markup.group(0))
        position = markup.end()
    parts.append(word_pattern.sub(substitute, text[position:]))
    return "".join(parts), counts


# `has_body`, not `has_simple_text_body`: the raw transcript this runs on first is an HTML
# item, and the stricter precondition refused it on the real pipeline while every test
# passed on plain-text fixtures. Tags and attributes are cut out below before replacing.
@kash_action(precondition=has_body)
def apply_transcript_replacements(item: Item) -> Item:
    """
    Correct recurring misrecognized words in the transcript body.

    Deepgram key terms raise the odds of a correct spelling without settling it. Measured
    on a five-hour interview with seventeen key terms supplied, `Omarchy` went from 4
    occurrences to 47 and `Amache` from 14 to 0, while `Omachi` still stood 19 times. That
    residue is in the transcript body, where processing instructions cannot reach it —
    they are read only by the overview stages. This runs before every other stage, so
    speaker correction, paragraphs, headings, the outline and the synopsis all read the
    corrected words.
    """
    if not item.body:
        raise InvalidInput(f"Item must have a body: {item}")

    replacements = get_replacements(item)
    body, counts = apply_replacements(item.body, replacements)
    total = sum(counts.values())
    if total:
        detail = ", ".join(f"{w}→{replacements[w]}: {n}" for w, n in counts.items() if n)
        log.message("Applied %s replacements (%s)", total, detail)
    else:
        log.warning(
            "No replacements matched the transcript: %s", ", ".join(sorted(replacements)) or "none"
        )
    return item.derived_copy(body=body)


def apply_replacements_if_any(item: Item) -> Item:
    """
    Run the correction stage only when the item carries a mapping.

    A run with no replacements must produce the output it produced before this stage
    existed, byte for byte, and it must not add a step to the workspace: an extra derived
    item would renumber every file after it and change the identity of the stages below.
    """
    if not get_replacements(item):
        return item
    return apply_transcript_replacements(item)


## Tests


SPAN = '<span class="speaker-label" data-speaker-id="0">SPEAKER 0:</span>'
"""A speaker label in the shape the raw transcript actually uses."""


def _replace(body: str, replacements: dict[str, str]) -> str:
    return apply_replacements(body, replacements)[0]


def test_replacements_are_whole_word_only() -> None:
    mapping = {"Omachi": "Omarchy"}

    assert _replace("Omachi is fast.", mapping) == "Omarchy is fast."
    assert _replace("Omachiland is not a place.", mapping) == "Omachiland is not a place."
    assert _replace("He said Omachi, then Omachi again.", mapping) == (
        "He said Omarchy, then Omarchy again."
    )
    # A word that merely contains the mapping key is left alone from either side.
    assert _replace("NotOmachi and Omachify", mapping) == "NotOmachi and Omachify"


def test_replacements_preserve_the_case_of_each_occurrence() -> None:
    mapping = {"Omachi": "Omarchy"}

    assert _replace("Omachi omachi OMACHI", mapping) == "Omarchy omarchy OMARCHY"


def test_a_lowercase_key_can_fix_capitalization() -> None:
    """An exact match of the key is answered verbatim, or `omakub: Omakub` could not work."""
    assert _replace("omakub is the old one.", {"omakub": "Omakub"}) == "Omakub is the old one."


def test_possessives_and_plurals_follow_the_word() -> None:
    mapping = {"Omachi": "Omarchy"}

    assert _replace("Omachi's release", mapping) == "Omarchy's release"
    assert _replace("Omachi’s release", mapping) == "Omarchy’s release"
    assert _replace("two Omachis", mapping) == "two Omarchys"


def test_text_inside_tags_and_attributes_is_never_touched() -> None:
    body = (
        '<span class="speaker-label" data-speaker-id="Omachi">Omachi:</span>\n'
        '<span data-timestamp="4.56">Omachi is fast.</span>'
    )

    result = _replace(body, {"Omachi": "Omarchy"})

    assert result == (
        '<span class="speaker-label" data-speaker-id="Omachi">Omarchy:</span>\n'
        '<span data-timestamp="4.56">Omarchy is fast.</span>'
    )
    assert 'data-speaker-id="Omachi"' in result
    assert 'data-timestamp="4.56"' in result


def test_an_html_comment_is_left_alone() -> None:
    body = "<!-- Omachi note -->\nOmachi is fast."

    assert _replace(body, {"Omachi": "Omarchy"}) == "<!-- Omachi note -->\nOmarchy is fast."


def test_an_empty_mapping_returns_the_text_unchanged() -> None:
    body = f'{SPAN}\n<span data-timestamp="4.56">Omachi is fast.</span>'

    text, counts = apply_replacements(body, {})

    assert text == body
    assert counts == {}


def test_a_mapping_cannot_cascade_through_its_own_output() -> None:
    """One pass, so `A -> B` and `B -> C` cannot turn an `A` into a `C`."""
    assert _replace("A and B", {"A": "B", "B": "C"}) == "B and C"


def test_counts_are_reported_per_entry() -> None:
    body = f'{SPAN}\n<span data-timestamp="4.56">Omachi, omachi, and Hansen.</span>'

    _, counts = apply_replacements(body, {"Omachi": "Omarchy", "Hansen": "Hansson"})

    assert counts == {"Omachi": 2, "Hansen": 1}


def test_the_stage_corrects_the_body_and_leaves_the_mapping_in_place() -> None:
    from inspect import unwrap

    from kash.model import Format, ItemType

    item = Item(
        type=ItemType.doc,
        format=Format.md_html,
        body=f'{SPAN}\n<span data-timestamp="4.56">Omachi is fast.</span>',
        extra={"transcription": {"replacements": {"Omachi": "Omarchy"}}},
    )

    result = unwrap(apply_transcript_replacements)(item)

    assert result.body is not None
    assert "Omarchy is fast." in result.body
    assert "Omachi is" not in result.body
    # The mapping rides along on the corrected item, which is what makes editing it re-run
    # this stage and everything below it.
    assert get_replacements(result) == {"Omachi": "Omarchy"}


def test_the_log_says_what_was_replaced_and_how_often(caplog: object) -> None:
    """
    The counts are the only evidence a run gives that the list did anything. A list that
    silently matched nothing looks exactly like one that worked.
    """
    import logging
    from inspect import unwrap
    from typing import cast

    import pytest
    from kash.model import Format, ItemType

    captured = cast("pytest.LogCaptureFixture", caplog)
    item = Item(
        type=ItemType.doc,
        format=Format.md_html,
        body=f'{SPAN}\n<span data-timestamp="4.56">Omachi, omachi, and Hansen.</span>',
        extra={"transcription": {"replacements": {"Omachi": "Omarchy", "Hansen": "Hansson"}}},
    )

    with captured.at_level(logging.INFO, logger=__name__):
        unwrap(apply_transcript_replacements)(item)

    said = [record.getMessage() for record in captured.records if record.name == __name__]
    assert "Applied 3 replacements (Omachi→Omarchy: 2, Hansen→Hansson: 1)" in said, said


def test_a_mapping_that_matches_nothing_is_reported_as_such(caplog: object) -> None:
    import logging
    from inspect import unwrap
    from typing import cast

    import pytest
    from kash.model import Format, ItemType

    captured = cast("pytest.LogCaptureFixture", caplog)
    item = Item(
        type=ItemType.doc,
        format=Format.md_html,
        body="Nothing here needs correcting.",
        extra={"transcription": {"replacements": {"Omachi": "Omarchy"}}},
    )

    with captured.at_level(logging.INFO, logger=__name__):
        unwrap(apply_transcript_replacements)(item)

    said = [record.getMessage() for record in captured.records if record.name == __name__]
    assert any("No replacements matched" in message and "Omachi" in message for message in said), (
        said
    )


def test_a_run_with_no_mapping_does_not_add_a_stage() -> None:
    from kash.model import Format, ItemType

    item = Item(type=ItemType.doc, format=Format.md_html, body="Omachi is fast.")

    assert apply_replacements_if_any(item) is item
