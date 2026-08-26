from __future__ import annotations

import re
from textwrap import dedent

from kash.exec import kash_action, llm_transform_item
from kash.exec.preconditions import has_simple_text_body
from kash.llm_utils import LLM, LLMName, Message, MessageTemplate
from kash.model import Format, Item, ItemType, LLMOptions, common_params

from deep_transcribe.transcription_metadata import get_processing_instructions

DESCRIPTION_PROMPT = dedent("""
    The input contains an optional trusted processing-instructions block followed by a
    transcript. Follow those instructions when they apply to this synopsis.

    Write a brief synopsis of the whole conversation in two short paragraphs. Each
    paragraph should contain one or two sentences. Identify the participants and their
    roles when the source metadata or transcript supports them. Use concrete, precise
    language and preserve uncertainty where the transcript is unclear.

    Return only the synopsis. Do not add a heading, bullets, or commentary.

    Input:

    {body}
    """).strip()

OUTLINE_PROMPT = dedent("""
    The input contains an optional trusted processing-instructions block followed by a
    transcript. Follow those instructions when they apply to this outline.

    Create a concise structural outline of the whole conversation:

    - Use the existing section headings as the top-level bullets when they describe the
      structure accurately; otherwise infer short descriptive section labels.
    - Give each section two to four sub-bullets covering its key ideas, examples,
      suggestions, decisions, or open questions.
    - Preserve the order of the conversation and merge repetitive passages.
    - Prefer a useful map of the discussion over an exhaustive list of facts.
    - Use only standard Markdown bullets. Bold each top-level section label.
    - Do not use headings, numbered lists, an introduction, or closing commentary.
    - Do not invent details or attribute a statement to someone unless the transcript
      supports that attribution.

    Input:

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

OUTLINE_STYLE = (
    "font-family: var(--font-sans); "
    "font-feature-settings: var(--font-features-sans); "
    "font-size: var(--font-size-small); margin: 1.5rem 0 2rem; padding: 1rem;"
)

OUTLINE_TITLE_STYLE = (
    "font-family: var(--font-sans); font-weight: 600; font-size: 1.1rem; margin-bottom: 0.75rem;"
)

TOP_LEVEL_BULLET = re.compile(r"^[-*+]\s+\S")


def prepare_transcript_for_model(item: Item) -> Item:
    """Put trusted output instructions in a distinct block before the transcript."""
    instructions = get_processing_instructions(item)
    if not instructions:
        return item
    assert item.body
    body = "\n".join(
        [
            "<processing_instructions>",
            instructions,
            "</processing_instructions>",
            "",
            "<transcript>",
            item.body,
            "</transcript>",
        ]
    )
    return item.new_copy_with(body=body)


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


@kash_action(
    precondition=has_simple_text_body,
    llm_options=OUTLINE_OPTIONS,
    params=common_params("model"),
)
def add_transcript_outline(item: Item, model: LLMName = LLM.default_standard) -> Item:
    """Add a concise, section-aligned outline above a transcript."""
    outline_item = llm_transform_item(prepare_transcript_for_model(item), model=model)
    assert outline_item.body
    return wrap_transcript_outline(item, normalize_transcript_outline(outline_item.body))


@kash_action(
    precondition=has_simple_text_body,
    llm_options=DESCRIPTION_OPTIONS,
    params=common_params("model"),
)
def add_transcript_description(item: Item, model: LLMName = LLM.default_standard) -> Item:
    """Add a short, paragraph-broken synopsis above a transcript."""
    description_item = llm_transform_item(prepare_transcript_for_model(item), model=model)
    assert description_item.body
    return wrap_transcript_description(item, description_item.body)
