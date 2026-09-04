from __future__ import annotations

import logging
import re
from textwrap import dedent

from kash.exec import kash_action, llm_transform_item
from kash.exec.preconditions import has_simple_text_body
from kash.llm_utils import LLM, LLMName, Message, MessageTemplate
from kash.model import Format, Item, ItemType, LLMOptions, common_params
from kash.utils.errors import ApiResultError

from deep_transcribe.chunking import split_body
from deep_transcribe.transcription_metadata import (
    get_processing_instructions,
    source_prompt_context,
)

DESCRIPTION_PROMPT = dedent("""
    The input contains an optional trusted processing-instructions block followed by a
    transcript. Apply only instructions relevant to the synopsis. Instructions about an
    outline or another stage must not change the output form requested here.

    Write a brief synopsis of the whole conversation in two short paragraphs. Each
    paragraph should contain one or two sentences. Identify the participants and their
    roles when the source metadata or transcript supports them. Use concrete, precise
    language and preserve uncertainty where the transcript is unclear.

    Return only the synopsis. Do not add a heading, bullets, or commentary.

    Input:

    {body}
    """).strip()

_OUTLINE_RULES = dedent("""
    - EVERY top-level bullet is a bold section label and nothing else. Every point about
      that section is an indented sub-bullet beneath it. Never write a point as a
      top-level bullet.
    - Use the existing section headings as the section labels when they describe the
      structure accurately; otherwise infer short descriptive labels.
    - Give each section two to four sub-bullets covering its key ideas, examples,
      suggestions, decisions, or open questions.
    - Preserve the order of the conversation and merge repetitive passages.
    - Prefer a useful map of the discussion over an exhaustive list of facts.
    - Use only standard Markdown bullets, two spaces of indent for sub-bullets.
    - Do not use headings, numbered lists, an introduction, or closing commentary.
    - Do not invent details or attribute a statement to someone unless the transcript
      supports that attribution.

    The shape, exactly:

    - **A section label**
      - A point about it
      - Another point
    - **The next section label**
      - A point about it
    """).strip()

OUTLINE_PROMPT = (
    dedent("""
    The input contains an optional trusted processing-instructions block followed by a
    transcript. Apply only instructions relevant to the outline. Instructions about a
    synopsis or another stage must not change the output form requested here.

    Create a concise structural outline of the whole conversation.

    {rules}

    Input:

    {{body}}
    """)
    .strip()
    .format(rules=_OUTLINE_RULES)
)

OUTLINE_CHUNK_PROMPT = (
    dedent("""
    The input contains an optional trusted processing-instructions block followed by ONE
    STRETCH of a longer transcript. Apply only instructions relevant to the outline.

    Outline this stretch, and only this stretch. The stretches before and after it are
    outlined separately and the parts are joined in order, so do not introduce the
    conversation, do not summarize it as a whole, and do not close it off.

    {rules}

    Input:

    {{body}}
    """)
    .strip()
    .format(rules=_OUTLINE_RULES)
)

CHUNK_SUMMARY_PROMPT = dedent("""
    The input contains an optional trusted processing-instructions block followed by one
    stretch of a longer transcript. Apply only instructions relevant to a summary.

    Summarize this stretch in two or three sentences. Name the participants and their
    roles where the transcript supports them, and say what is actually covered rather
    than that a discussion took place. Do not refer to "this segment" or "this excerpt";
    write as if describing part of a conversation.

    Return only the summary. Do not add a heading, bullets, or commentary.

    Input:

    {body}
    """).strip()

SYNOPSIS_REDUCE_PROMPT = dedent("""
    Below are summaries of consecutive stretches of one recorded conversation, in order.
    They are all you have of it, and together they describe the whole thing.

    Write a brief synopsis of the whole conversation in two short paragraphs. Each
    paragraph should contain one or two sentences. Identify the participants and their
    roles when the summaries support them. Use concrete, precise language, preserve
    uncertainty, and cover the arc of the conversation rather than only its opening.

    Return only the synopsis. Do not add a heading, bullets, or commentary.

    Summaries, in order:

    {body}
    """).strip()

SYSTEM_MESSAGE = Message(
    "You are a careful transcript editor. Return exactly the requested result."
)

DESCRIPTION_OPTIONS = LLMOptions(
    use_item_context=True,
    system_message=SYSTEM_MESSAGE,
    body_template=MessageTemplate(DESCRIPTION_PROMPT),
)

OUTLINE_OPTIONS = LLMOptions(
    use_item_context=True,
    system_message=SYSTEM_MESSAGE,
    body_template=MessageTemplate(OUTLINE_PROMPT),
)

OUTLINE_CHUNK_OPTIONS = LLMOptions(
    use_item_context=True,
    system_message=SYSTEM_MESSAGE,
    body_template=MessageTemplate(OUTLINE_CHUNK_PROMPT),
)

CHUNK_SUMMARY_OPTIONS = LLMOptions(
    use_item_context=True,
    system_message=SYSTEM_MESSAGE,
    body_template=MessageTemplate(CHUNK_SUMMARY_PROMPT),
)

SYNOPSIS_REDUCE_OPTIONS = LLMOptions(
    use_item_context=True,
    system_message=SYSTEM_MESSAGE,
    body_template=MessageTemplate(SYNOPSIS_REDUCE_PROMPT),
)

OUTLINE_STYLE = (
    "font-family: var(--font-sans); "
    "font-feature-settings: var(--font-features-sans); "
    "font-size: var(--font-size-small); margin: 1.5rem 0 2rem; padding: 1rem;"
)

OUTLINE_TITLE_STYLE = (
    "font-family: var(--font-sans); font-weight: 600; font-size: 1.1rem; margin-bottom: 0.75rem;"
)

TOP_LEVEL_BULLET = re.compile(r"^[-*+]\s+\S")

log = logging.getLogger(__name__)


def prepare_transcript_for_model(item: Item, body: str | None = None) -> Item:
    """
    Put source evidence and trusted output instructions in distinct prompt blocks.

    `body` overrides the transcript with one chunk of it, so a stage that runs per chunk
    still carries the same instructions and source context into every call.
    """
    instructions = get_processing_instructions(item)
    assert item.body
    transcript = body if body is not None else item.body
    body_parts: list[str] = []
    if instructions:
        body_parts.extend(
            [
                "<processing_instructions>",
                instructions,
                "</processing_instructions>",
                "",
            ]
        )
    body_parts.extend(["<transcript>", transcript, "</transcript>"])
    return item.new_copy_with(
        body="\n".join(body_parts),
        title=None,
        description=None,
        additional_context=source_prompt_context(item) or None,
    )


def wrap_transcript_outline(item: Item, outline: str) -> Item:
    """Place an always-visible structural outline above the transcript."""
    assert item.body
    body = "\n\n".join(
        [
            f'<div class="transcript-outline" style="{OUTLINE_STYLE}">',
            (f'<div class="transcript-outline-title" style="{OUTLINE_TITLE_STYLE}">Outline</div>'),
            outline,
            "</div>",
            '<div class="original">',
            item.body,
            "</div>",
        ]
    )
    return item.derived_copy(type=ItemType.doc, format=Format.md_html, body=body)


def normalize_transcript_outline(response: str) -> str:
    """Keep the Markdown outline even when a model adds an unwanted preamble."""
    lines = response.strip().splitlines()
    first_bullet = next(
        (index for index, line in enumerate(lines) if TOP_LEVEL_BULLET.match(line)),
        None,
    )
    if first_bullet is None:
        raise ValueError("Transcript outline did not contain a top-level Markdown bullet")
    return "\n".join(lines[first_bullet:]).strip()


def wrap_transcript_description(item: Item, description: str) -> Item:
    """Place the brief synopsis above the outline and transcript."""
    assert item.body
    body = "\n\n".join(
        [
            '<div class="description">',
            description,
            "</div>",
            '<div class="original">',
            item.body,
            "</div>",
        ]
    )
    return item.derived_copy(type=ItemType.doc, format=Format.md_html, body=body)


def _complete(model: LLMName, options: LLMOptions, prepared: Item) -> str:
    """
    One completion under explicit options, for the passes whose prompt is not the action's.

    Folds in the same bounded source metadata `llm_transform_item` would, so a chunk call
    can still name participants and disambiguate terms from the source.
    """
    from kash.exec.llm_transforms import llm_options_with_item_context
    from kash.llm_utils.fuzzy_parsing import strip_markdown_fence
    from kash.llm_utils.llm_completion import llm_template_completion

    resolved = (
        llm_options_with_item_context(options, prepared) if options.use_item_context else options
    )
    result = llm_template_completion(
        model=model,
        system_message=resolved.system_message or SYSTEM_MESSAGE,
        input=prepared.body or "",
        body_template=resolved.body_template,
    ).content
    return strip_markdown_fence(result).strip()


@kash_action(
    precondition=has_simple_text_body,
    output_type=ItemType.doc,
    output_format=Format.md_html,
    llm_options=OUTLINE_OPTIONS,
    params=common_params("model"),
)
def add_transcript_outline(item: Item, model: LLMName = LLM.default_standard) -> Item:
    """
    Add a concise, section-aligned outline above a transcript.

    The outline is already sectional, so a long recording is outlined a chunk at a time
    and the parts concatenate in timeline order with nothing to reconcile — each chunk
    covers a disjoint stretch and keeps its own headings. Short media is one chunk and
    one call, exactly as before.
    """
    assert item.body
    chunks = split_body(item.body)
    parts: list[str] = []
    for position, chunk in enumerate(chunks):
        prepared = prepare_transcript_for_model(item, chunk)
        # A chunk is not the whole conversation and must not be outlined as one, so the
        # chunked path uses its own prompt rather than the action's.
        response = (
            _complete(model, OUTLINE_CHUNK_OPTIONS, prepared)
            if len(chunks) > 1
            else llm_transform_item(prepared, model=model, format=Format.md_html).body
        )
        assert response
        try:
            parts.append(normalize_transcript_outline(response))
        except ValueError:
            # One chunk that comes back without bullets costs its stretch of the
            # outline, not the whole outline.
            log.warning(
                "Outline chunk %d/%d produced no bullets, skipping it",
                position + 1,
                len(chunks),
            )
    if not parts:
        raise ValueError("Transcript outline did not contain a top-level Markdown bullet")
    return wrap_transcript_outline(item, "\n".join(parts))


@kash_action(
    precondition=has_simple_text_body,
    output_type=ItemType.doc,
    output_format=Format.md_html,
    llm_options=DESCRIPTION_OPTIONS,
    params=common_params("model"),
)
def add_transcript_description(item: Item, model: LLMName = LLM.default_standard) -> Item:
    """
    Add a short, paragraph-broken synopsis above a transcript.

    A synopsis is about the whole recording, so unlike the outline it cannot simply be
    concatenated. A long recording is summarized a chunk at a time and those summaries
    are reduced into the two paragraphs. The reduce reads a few thousand words whatever
    the recording's length, so it has no ceiling. Short media takes the direct path and
    is unchanged.
    """
    assert item.body
    chunks = split_body(item.body)
    if len(chunks) <= 1:
        description_item = llm_transform_item(
            prepare_transcript_for_model(item),
            model=model,
            format=Format.md_html,
        )
        assert description_item.body
        return wrap_transcript_description(item, description_item.body)

    log.info("Summarizing %d chunk(s) before reducing to a synopsis", len(chunks))
    summaries = [
        _complete(model, CHUNK_SUMMARY_OPTIONS, prepare_transcript_for_model(item, chunk))
        for chunk in chunks
    ]
    kept = [summary for summary in (s.strip() for s in summaries) if summary]
    if not kept:
        raise ApiResultError("No chunk summaries to reduce into a synopsis")
    numbered = "\n\n".join(f"{i + 1}. {summary}" for i, summary in enumerate(kept))
    # The reduce reads the summaries, not the transcript, so it is article-sized at any
    # recording length. It keeps the source metadata so it can still name participants.
    reduced = _complete(
        model,
        SYNOPSIS_REDUCE_OPTIONS,
        prepare_transcript_for_model(item, numbered).new_copy_with(body=numbered),
    )
    return wrap_transcript_description(item, reduced)
