"""Enforce paragraph formatting's whitespace-only contract after window stitching."""

import re

from chopdiff.transforms import changes_whitespace, filtered_transform
from chopdiff.transforms.window_settings import WINDOW_BR
from flexdoc import FlexDoc
from kash.config.logger import get_logger
from kash.exec import kash_action
from kash.exec.preconditions import has_simple_text_body
from kash.model import TWO_ARGS, ActionInput, ActionResult
from kash.utils.errors import InvalidInput

log = get_logger(__name__)


def _without_whitespace(text: str) -> str:
    return re.sub(r"\s+", "", text)


def repair_paragraph_body(source: str, formatted: str) -> str:
    """Keep paragraph breaks while restoring the complete source's exact spoken text."""
    candidate = formatted.replace(WINDOW_BR, "")
    if _without_whitespace(candidate) == _without_whitespace(source):
        return candidate

    # A window can pass its own diff filter and still be duplicated during stitching.
    # Reuse the same filter once over the whole transcript so genuine source repetitions
    # survive, and rejected model edits are restored from the source as well.
    repaired = filtered_transform(
        FlexDoc.from_text(source),
        lambda _: FlexDoc.from_text(candidate),
        None,
        changes_whitespace,
    ).reassemble()
    if _without_whitespace(repaired) != _without_whitespace(source):
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
