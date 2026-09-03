from __future__ import annotations

import json
import logging
from textwrap import dedent
from typing import Any, cast

from kash.exec import kash_action
from kash.exec.preconditions import has_simple_text_body, has_timestamps
from kash.llm_utils import LLM, LLMName, Message, MessageTemplate
from kash.llm_utils.fuzzy_parsing import fuzzy_parse_json
from kash.model import Item, ItemType, Param, common_params
from kash.utils.errors import ApiResultError, InvalidInput

from deep_transcribe.transcript_index import (
    CONCEPT_KINDS,
    CONCEPT_RELATION_TYPES,
    scan_raw_units,
)

log = logging.getLogger(__name__)

CONCEPTS_KEY = "concepts"
"""Key under `extra.transcription` where extracted concepts are stored."""

MAX_CONCEPTS = 24
"""Upper bound on extracted concepts, so the ribbon and graph stay legible."""

EXTRACTION_PROMPT = dedent("""
    You are given a transcript as numbered turns, each with a citation key (its start
    time in seconds) and a speaker. Extract the key concepts of the conversation.

    A concept is a topic, entity, term, claim, or decision that the conversation
    actually discusses. Prefer a short list of load-bearing concepts over an
    exhaustive inventory; at most {max_concepts}.

    Return ONLY a JSON object of this exact shape:

    {{"concepts": [
      {{
        "id": "kebab-case-slug",
        "label": "Short display label",
        "kind": "topic|entity|term|claim|decision",
        "gloss": "One sentence saying what this is and why it matters here.",
        "mentions": ["<citation key>", "<citation key>"],
        "relations": [{{"to": "other-concept-id", "type": "leads-to|contrasts-with|elaborates|example-of|depends-on"}}]{research_field}
      }}
    ]}}

    Rules:
    - Every mention MUST be one of the citation keys shown in the transcript below,
      copied exactly. List the turns where the concept is actually discussed.
    - Base every concept and gloss only on the transcript{search_clause}. Do not add
      outside facts to glosses.
    - Relations are optional and must use only the listed types and other concept ids.
    - Capture the most consequential claims and decisions speakers make as kind
      "claim" or "decision", wording each gloss as what is asserted or decided and by
      whom.
    - Use each id once.
    {research_rules}
    Transcript turns:

    {turns}
    """).strip()

RESEARCH_FIELD = (
    ',\n        "research": {"summary": "1-3 sentences of background.", "sources": ["url"]}'
)

RESEARCH_RULES = dedent("""
    - The research field is optional background from web search: only include it when
      search results from reliable sources corroborate it, always cite the source URLs,
      and never let search introduce a concept the transcript does not establish.
    """).strip()


def _format_turns(body: str) -> str:
    lines: list[str] = []
    for unit in scan_raw_units(body):
        speaker = f"{unit.label}: " if unit.label else ""
        text = " ".join(unit.text.split())
        lines.append(f"[key={unit.key}] {speaker}{text}")
    return "\n".join(lines)


def _parse_concepts(response: str) -> list[dict[str, Any]]:
    try:
        parsed = fuzzy_parse_json(response)
    except json.JSONDecodeError as error:
        raise ApiResultError(f"Could not parse extracted concepts: {error}") from error
    if isinstance(parsed, list):
        raw_list = cast(list[object], parsed)
    elif isinstance(parsed, dict):
        raw_list_obj = cast(dict[object, object], parsed).get("concepts")
        if not isinstance(raw_list_obj, list):
            raise ApiResultError(f"Concept response has no concepts list: {response[:200]}")
        raw_list = cast(list[object], raw_list_obj)
    else:
        raise ApiResultError(f"Concept response is not a JSON object: {response[:200]}")

    concepts: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for raw in raw_list[:MAX_CONCEPTS]:
        if not isinstance(raw, dict):
            continue
        concept = cast(dict[str, Any], raw)
        concept_id = str(concept.get("id") or "").strip()
        if not concept_id or concept_id in seen_ids:
            log.warning("Skipping concept with missing or duplicate id: %r", concept_id)
            continue
        seen_ids.add(concept_id)
        kind = str(concept.get("kind") or "topic")
        raw_mentions = concept.get("mentions")
        mentions = (
            [str(m) for m in cast(list[object], raw_mentions)]
            if isinstance(raw_mentions, list)
            else []
        )
        raw_relations = concept.get("relations")
        relations = [
            cast(dict[str, Any], r)
            for r in (cast(list[object], raw_relations) if isinstance(raw_relations, list) else [])
            if isinstance(r, dict)
            and str(cast(dict[str, Any], r).get("type")) in CONCEPT_RELATION_TYPES
        ]
        concepts.append(
            {
                "id": concept_id,
                "label": str(concept.get("label") or concept_id),
                "kind": kind if kind in CONCEPT_KINDS else "topic",
                "gloss": str(concept.get("gloss") or ""),
                "mentions": mentions,
                "relations": relations,
                "research": concept.get("research"),
            }
        )
    return concepts


WEB_SEARCH_PARAM = Param(
    name="web_search",
    description="Allow concept research notes corroborated by web search.",
    type=bool,
    default_value=False,
)


@kash_action(
    precondition=has_simple_text_body & has_timestamps,
    params=(*common_params("model"), WEB_SEARCH_PARAM),
)
def extract_transcript_concepts(
    item: Item,
    model: LLMName = LLM.default_structured,
    web_search: bool = False,
) -> Item:
    """
    Extract a concept map from the transcript into item metadata.

    Concepts cite citation keys that already exist in the document; the index stage
    validates every mention and derives spans and speakers, so nothing here can
    assert timing the transcript does not support.
    """
    from kash.llm_utils.llm_completion import llm_template_completion

    if not item.body:
        raise InvalidInput(f"Item must have a body: {item}")
    turns = _format_turns(item.body)
    if not turns:
        log.warning("No citation-anchored turns found; skipping concept extraction")
        return item.derived_copy(type=ItemType.doc)

    prompt = EXTRACTION_PROMPT.format(
        max_concepts=MAX_CONCEPTS,
        research_field=RESEARCH_FIELD if web_search else "",
        research_rules=RESEARCH_RULES + "\n" if web_search else "",
        search_clause=" and web results you corroborate" if web_search else "",
        turns=turns,
    )
    escaped_prompt = prompt.replace("{", "{{").replace("}", "}}")
    response = llm_template_completion(
        model=model,
        system_message=Message(
            "You map the concepts of a transcript conservatively, asserting only what "
            "the transcript supports."
        ),
        input="Extract the concept map for the supplied transcript.",
        body_template=MessageTemplate(escaped_prompt + "\n\n{body}"),
        enable_web_search=web_search,
    ).content
    concepts = _parse_concepts(response)
    if not concepts:
        return item.derived_copy(type=ItemType.doc)

    item_extra = cast(dict[str, object], item.extra or {}).copy()
    raw_transcription = item_extra.get("transcription")
    transcription = (
        cast(dict[str, object], raw_transcription).copy()
        if isinstance(raw_transcription, dict)
        else {}
    )
    transcription[CONCEPTS_KEY] = concepts
    item_extra["transcription"] = transcription
    return item.derived_copy(type=ItemType.doc, extra=item_extra)


## Tests


def test_parse_concepts_filters_and_normalizes() -> None:
    response = json.dumps(
        {
            "concepts": [
                {
                    "id": "suite-upgrade",
                    "label": "Suite upgrade",
                    "kind": "decision",
                    "gloss": "The fix for the lost booking.",
                    "mentions": ["36.03", "60.82"],
                    "relations": [
                        {"to": "reservation-glitch", "type": "leads-to"},
                        {"to": "reservation-glitch", "type": "not-a-type"},
                    ],
                },
                {"id": "suite-upgrade", "label": "duplicate"},
                {"id": "", "label": "missing id"},
                {"id": "weird-kind", "kind": "banana", "mentions": ["1.00"]},
            ]
        }
    )

    concepts = _parse_concepts(response)

    assert [c["id"] for c in concepts] == ["suite-upgrade", "weird-kind"]
    assert concepts[0]["relations"] == [{"to": "reservation-glitch", "type": "leads-to"}]
    assert concepts[1]["kind"] == "topic"


def test_format_turns_uses_citation_keys() -> None:
    body = (
        "**Alice:** Hello there.\n"
        '<span class="citation timestamp-link" data-src="r.yml" data-timestamp="1.00">'
        '<a href="https://example.com?t=1s">00:01</a></span>\n'
    )

    turns = _format_turns(body)

    assert turns == "[key=1.00] Alice: Hello there."


def test_concepts_roundtrip_through_index() -> None:
    from deep_transcribe.transcript_index import build_transcript_index

    body = (
        "**Alice:** First point.\n"
        '<span class="citation timestamp-link" data-src="r.yml" data-timestamp="1.00">'
        '<a href="https://example.com?t=1s">00:01</a></span>\n\n'
        "**Bob:** Second point.\n"
        '<span class="citation timestamp-link" data-src="r.yml" data-timestamp="5.00">'
        '<a href="https://example.com?t=5s">00:05</a></span>\n'
    )
    concepts: list[dict[str, object]] = [
        {
            "id": "first-point",
            "label": "First point",
            "kind": "claim",
            "gloss": "g",
            "mentions": ["1.00", "99.00"],
            "relations": [{"to": "missing-concept", "type": "leads-to"}],
            "research": None,
        }
    ]

    index = build_transcript_index(body, roster=["Alice", "Bob"], duration=10.0, concepts=concepts)
    resolved = index.to_json_dict()["concepts"]

    assert isinstance(resolved, list)
    only = resolved[0]
    assert only["mentions"] == [{"t": 1.0, "key": "1.00"}]
    assert only["span"] == [1.0, 5.0]
    assert only["speakers"] == ["s0"]
    assert only["relations"] == []  # relation target doesn't exist
