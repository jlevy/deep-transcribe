"""Enforce paragraph formatting's whitespace-only contract after window stitching."""

import re
from collections.abc import Iterable

from chopdiff.transforms import changes_whitespace, filtered_transform
from chopdiff.transforms.window_settings import WINDOW_BR
from flexdoc import FlexDoc
from kash.config.logger import get_logger
from kash.exec import kash_action
from kash.exec.preconditions import has_simple_text_body
from kash.model import TWO_ARGS, ActionInput, ActionResult
from kash.utils.errors import InvalidInput

log = get_logger(__name__)

# The word diff can be quadratic on repetitive text. Use the original source for any
# changed span that still exceeds this budget after removing its matching surroundings.
_MAX_DIFF_CHARS = 30_000
_CONTEXT_WORDS = 8


def _without_whitespace(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _common_word_count(left: Iterable[re.Match[str]], right: Iterable[re.Match[str]]) -> int:
    count = 0
    for left_word, right_word in zip(left, right, strict=False):
        if left_word[0] != right_word[0]:
            break
        count += 1
    return count


def _changed_spans(source: str, candidate: str) -> tuple[slice, slice]:
    """Find the changed word span on each side, with context for the bounded diff."""
    source_words = list(re.finditer(r"\S+", source))
    candidate_words = list(re.finditer(r"\S+", candidate))
    prefix = _common_word_count(source_words, candidate_words)
    suffix = min(
        _common_word_count(reversed(source_words), reversed(candidate_words)),
        min(len(source_words), len(candidate_words)) - prefix,
    )
    shared_prefix = max(0, prefix - _CONTEXT_WORDS)
    shared_suffix = max(0, suffix - _CONTEXT_WORDS)

    def changed_span(words: list[re.Match[str]]) -> slice:
        start = words[shared_prefix].start() if shared_prefix else 0
        stop = words[-shared_suffix - 1].end() if shared_suffix else None
        return slice(start, stop)

    return changed_span(source_words), changed_span(candidate_words)


def repair_paragraph_body(source: str, formatted: str) -> str:
    """Keep paragraph breaks while restoring the complete source's exact spoken text."""
    candidate = formatted.replace(WINDOW_BR, "")
    source_text = _without_whitespace(source)
    if _without_whitespace(candidate) == source_text:
        return candidate

    # A window can pass its own diff filter and still be duplicated during stitching.
    # Keep matching surroundings and run the same filter on the changed span.
    source_span, candidate_span = slice(None), slice(None)
    if max(len(source), len(candidate)) > _MAX_DIFF_CHARS:
        source_span, candidate_span = _changed_spans(source, candidate)
    source_change = source[source_span]
    candidate_change = candidate[candidate_span]
    if max(len(source_change), len(candidate_change)) <= _MAX_DIFF_CHARS:
        repaired_change = filtered_transform(
            FlexDoc.from_text(source_change),
            lambda _: FlexDoc.from_text(candidate_change),
            None,
            changes_whitespace,
        ).reassemble()
    else:
        repaired_change = source_change
    suffix = candidate[candidate_span.stop :] if candidate_span.stop is not None else ""
    repaired = candidate[: candidate_span.start or 0] + repaired_change + suffix
    if _without_whitespace(repaired) != source_text:
        log.warning(
            "Paragraph formatting could not preserve the source transcript; "
            "using the complete source with its original paragraph breaks."
        )
        return source
    log.warning(
        "Rejected non-whitespace changes in paragraph formatting; "
        "restored source text while retaining accepted paragraph breaks."
    )
    return repaired


@kash_action(expected_args=TWO_ARGS, run_per_item=False, precondition=has_simple_text_body)
def repair_paragraph_windows(action_input: ActionInput) -> ActionResult:
    """Validate paragraphized text against its source without repeating the paid action."""
    source, formatted = action_input.items
    if not source.body or not formatted.body:
        raise InvalidInput("Paragraph repair requires both the source and formatted transcript.")
    body = repair_paragraph_body(source.body, formatted.body)
    return ActionResult([formatted.derived_copy(body=body)])
