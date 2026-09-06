from __future__ import annotations

import re
from collections.abc import Collection
from dataclasses import dataclass
from functools import cache

from kash.config.logger import get_logger
from kash.exec import kash_action
from kash.exec.preconditions import has_html_body, has_simple_text_body
from kash.model import Format, Item, ItemType
from kash.utils.errors import InvalidInput

log = get_logger(__name__)

_ADJACENT_TIMESTAMP_SPAN_PATTERN = re.compile(
    r"(</span>)[ \t\r\n]+(?=<span\b(?=[^>]*\bdata-timestamp=))"
)

# A speaker turn, once the transcript is Markdown: `**DHH:** text…` opening a paragraph.
_SPEAKER_TURN_PATTERN = re.compile(
    r"\*\*(?P<speaker>[^*\n]{1,80}?):\*\*[ \t]*(?P<text>.*)\Z", re.DOTALL
)

# Paragraph breaks: one blank line, or several.
_PARA_BREAK_PATTERN = re.compile(r"(\n[ \t]*\n[ \t\n]*)")

# Anything that is not a letter or digit is punctuation for matching purposes, so
# "Mm-hmm." and "mm hmm" both reduce to "mm hmm".
_NON_WORD_PATTERN = re.compile(r"[^0-9a-z]+")

# Windowed LLM stages leave `<!--window-br-->` markers at some paragraph starts. They are
# not content, so look past them when deciding what a paragraph is.
_LEADING_COMMENT_PATTERN = re.compile(r"\A(?:<!--.*?-->[ \t\r\n]*)+", re.DOTALL)

# Blocks that must never receive an aside appended to them.
_NON_PROSE_PREFIXES = ("#", ">", "```", "~~~", "|", "<", "- ", "* ", "+ ")
_ORDERED_LIST_PATTERN = re.compile(r"\d+[.)] ")

DEFAULT_BACK_CHANNEL_TOKENS: frozenset[str] = frozenset(
    {
        "mhmm",
        "mm-hmm",
        "mmhmm",
        "uh-huh",
        "uh huh",
        "yeah",
        "yep",
        "yes",
        "right",
        "okay",
        "ok",
        "sure",
        "exactly",
        "totally",
        "wow",
        "so",
        "and",
        "um",
    }
)
"""Words that carry no content on their own, so a turn made only of them is a back-channel."""


@kash_action(precondition=has_html_body)
def normalize_transcript_fragments(item: Item) -> Item:
    """Remove false paragraph boundaries between timestamp spans in one speaker turn."""
    if not item.body:
        raise InvalidInput(f"Item must have a body: {item}")

    body = _ADJACENT_TIMESTAMP_SPAN_PATTERN.sub(r"\1 ", item.body)
    return item.derived_copy(body=body)


@kash_action(precondition=has_simple_text_body)
def fold_back_channel_turns(item: Item) -> Item:
    """Fold turns that are only an acknowledgement into the previous paragraph."""
    if not item.body:
        raise InvalidInput(f"Item must have a body: {item}")

    body, folded = fold_back_channels(item.body)
    log.message("Folded %s back-channel turns into the preceding paragraph.", folded)
    return item.derived_copy(body=body)


def _normalize_phrase(text: str) -> str:
    """Reduce a turn to lowercase words, so punctuation and hyphens stop mattering."""
    return _NON_WORD_PATTERN.sub(" ", text.lower()).strip()


@cache
def _back_channel_vocabulary(tokens: frozenset[str]) -> tuple[frozenset[str], frozenset[str]]:
    """Split the configured list into whole phrases and the single words that can pair up."""
    phrases = {phrase for phrase in (_normalize_phrase(token) for token in tokens) if phrase}
    singles = {phrase for phrase in phrases if " " not in phrase}
    return frozenset(phrases), frozenset(singles)


def is_back_channel(text: str, tokens: Collection[str] = DEFAULT_BACK_CHANNEL_TOKENS) -> bool:
    """
    True if `text` is nothing but acknowledgement: one word from `tokens`, or two of them.
    Three words or more always count as content, however filler-like they look.
    """
    phrases, singles = _back_channel_vocabulary(frozenset(tokens))
    phrase = _normalize_phrase(text)
    if not phrase:
        return False
    if phrase in phrases:
        return True
    words = phrase.split()
    return len(words) == 2 and all(word in singles for word in words)


@dataclass
class _Block:
    """One Markdown paragraph plus the break that follows it."""

    text: str
    sep: str

    @property
    def content(self) -> str:
        """The block's text without the windowing markers that can open it."""
        return _LEADING_COMMENT_PATTERN.sub("", self.text.strip()).strip()

    @property
    def turn(self) -> re.Match[str] | None:
        return _SPEAKER_TURN_PATTERN.fullmatch(self.content)

    @property
    def can_receive_aside(self) -> bool:
        content = self.content
        if not content:
            return False
        if content.startswith(_NON_PROSE_PREFIXES) or _ORDERED_LIST_PATTERN.match(content):
            return False
        return True


def fold_back_channels(
    body: str, tokens: Collection[str] = DEFAULT_BACK_CHANNEL_TOKENS
) -> tuple[str, int]:
    """
    Fold every all-acknowledgement speaker turn into the end of the previous paragraph as a
    bracketed, attributed aside, and return the new body with the number of turns folded.

    A back-channel that opens the document has nothing to fold into, so it stays as it is.
    So does one whose own turn continues into a following paragraph, since dropping its
    label would hand that paragraph to the wrong speaker.
    """
    # Hold the document's final newlines aside so folding a closing turn cannot eat them.
    text, trailer = body.rstrip(), body[len(body.rstrip()) :]
    pieces = _PARA_BREAK_PATTERN.split(text)
    blocks = [
        _Block(text=pieces[i], sep=pieces[i + 1] if i + 1 < len(pieces) else "")
        for i in range(0, len(pieces), 2)
    ]

    kept: list[_Block] = []
    folded = 0
    for index, block in enumerate(blocks):
        turn = block.turn
        following = blocks[index + 1] if index + 1 < len(blocks) else None
        continues_turn = (
            following is not None and bool(following.content) and following.turn is None
        )
        if (
            turn is None
            or continues_turn
            or not is_back_channel(turn["text"], tokens)
            or not kept
            or not kept[-1].can_receive_aside
        ):
            kept.append(block)
            continue

        aside = f"[{turn['speaker'].strip()}: {' '.join(turn['text'].split())}]"
        kept[-1].text = f"{kept[-1].text.rstrip()} {aside}"
        kept[-1].sep = block.sep
        folded += 1

    return "".join(block.text + block.sep for block in kept) + trailer, folded


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


def test_is_back_channel_takes_one_or_two_filler_words_only() -> None:
    assert is_back_channel("Mhmm.")
    assert is_back_channel("So")
    assert is_back_channel("Uh huh.")
    assert is_back_channel("Uh-huh.")
    assert is_back_channel("Mm-hmm.")
    assert is_back_channel("Right. Okay.")
    assert is_back_channel("Yeah, yeah!")

    assert not is_back_channel("And colors.\nYes.")
    assert not is_back_channel("Great regression.")
    assert not is_back_channel("Nice.")
    assert not is_back_channel("")


def test_fold_back_channels_attributes_the_aside_and_drops_the_turn() -> None:
    body = (
        "**DHH:** Everything turned from, like, this glamour, the pop.\n\n"
        "**Lex Fridman:** Mhmm.\n\n"
        "**DHH:** They niche in, you know, this idea of eternal recurrence.\n"
    )

    result, folded = fold_back_channels(body)

    assert folded == 1
    assert result == (
        "**DHH:** Everything turned from, like, this glamour, the pop. [Lex Fridman: Mhmm.]\n\n"
        "**DHH:** They niche in, you know, this idea of eternal recurrence.\n"
    )


def test_fold_back_channels_handles_bare_and_two_word_turns() -> None:
    body = (
        "**Lex Fridman:** Great regression.\n\n"
        "**DHH:** So\n\n"
        "**Lex Fridman:** They niche in, you know, this idea of eternal recurrence.\n\n"
        "**DHH:** Uh huh.\n\n"
        "**Lex Fridman:** And that is the whole point.\n"
    )

    result, folded = fold_back_channels(body)

    assert folded == 2
    assert result == (
        "**Lex Fridman:** Great regression. [DHH: So]\n\n"
        "**Lex Fridman:** They niche in, you know, this idea of eternal recurrence. "
        "[DHH: Uh huh.]\n\n"
        "**Lex Fridman:** And that is the whole point.\n"
    )


def test_fold_back_channels_leaves_longer_turns_alone() -> None:
    body = (
        "**Lex Fridman:** Great regression.\n\n"
        "**DHH:** And colors.\nYes.\n\n"
        "**Lex Fridman:** That is the whole point.\n"
    )

    result, folded = fold_back_channels(body)

    assert folded == 0
    assert result == body


def test_fold_back_channels_leaves_a_document_opening_back_channel() -> None:
    body = "**DHH:** Mhmm.\n\n**Lex Fridman:** Great regression.\n"

    result, folded = fold_back_channels(body)

    assert folded == 0
    assert result == body


def test_fold_back_channels_keeps_a_turn_that_continues_into_a_paragraph() -> None:
    # A folded label would hand the continuation paragraph to the wrong speaker.
    body = (
        "**Lex Fridman:** Great regression.\n\n"
        "**DHH:** Yeah.\n\n"
        "So the thing about eternal recurrence is that it keeps coming back.\n\n"
        "**Lex Fridman:** That is the whole point.\n"
    )

    result, folded = fold_back_channels(body)

    assert folded == 0
    assert result == body


def test_fold_back_channels_sees_past_windowing_markers() -> None:
    body = (
        "**Lex Fridman:** Great regression.\n\n"
        "<!--window-br--> **DHH:** Mhmm.\n\n"
        "**Lex Fridman:** That is the whole point.\n"
    )

    result, folded = fold_back_channels(body)

    assert folded == 1
    assert result == (
        "**Lex Fridman:** Great regression. [DHH: Mhmm.]\n\n"
        "**Lex Fridman:** That is the whole point.\n"
    )


def test_fold_back_channels_folds_runs_of_acknowledgements_in_order() -> None:
    body = (
        "**Lex Fridman:** Great regression.\n\n"
        "**DHH:** Mhmm.\n\n"
        "**Lex Fridman:** Yeah.\n\n"
        "**DHH:** They niche in.\n"
    )

    result, folded = fold_back_channels(body)

    assert folded == 2
    assert result == (
        "**Lex Fridman:** Great regression. [DHH: Mhmm.] [Lex Fridman: Yeah.]\n\n"
        "**DHH:** They niche in.\n"
    )


def test_fold_back_channels_respects_a_narrowed_token_list() -> None:
    body = (
        "**Lex Fridman:** Great regression.\n\n"
        "**DHH:** Mhmm.\n\n"
        "**Lex Fridman:** Yeah.\n\n"
        "**DHH:** They niche in.\n"
    )

    result, folded = fold_back_channels(body, tokens={"mhmm"})

    assert folded == 1
    assert result == (
        "**Lex Fridman:** Great regression. [DHH: Mhmm.]\n\n"
        "**Lex Fridman:** Yeah.\n\n"
        "**DHH:** They niche in.\n"
    )


def test_fold_back_channel_turns_action_folds_and_keeps_the_trailing_newline() -> None:
    from inspect import unwrap

    item = Item(
        type=ItemType.doc,
        format=Format.markdown,
        body=(
            "**DHH:** Everything turned from, like, this glamour, the pop.\n\n"
            "**Lex Fridman:** Mhmm.\n"
        ),
    )

    result = unwrap(fold_back_channel_turns)(item)

    assert result.body == (
        "**DHH:** Everything turned from, like, this glamour, the pop. [Lex Fridman: Mhmm.]\n"
    )
