from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from textwrap import dedent
from typing import Any, cast

from kash.exec import kash_action
from kash.exec.preconditions import has_simple_text_body, has_timestamps
from kash.llm_utils import LLM, LLMName, Message, MessageTemplate
from kash.llm_utils.fuzzy_parsing import fuzzy_parse_json
from kash.model import Item, ItemType, Param, common_params
from kash.utils.errors import ApiResultError, InvalidInput

from deep_transcribe.transcript_index import (
    CONCEPT_RELATION_TYPES,
    RawUnit,
    normalize_concept_kind,
    scan_raw_units,
)

log = logging.getLogger(__name__)

CONCEPTS_KEY = "concepts"
"""Key under `extra.transcription` where extracted concepts are stored."""

MAX_CONCEPTS_PER_CHUNK = 12
"""
Concept budget for one chunk, not for one recording.

A single budget applied to the whole document gives a long recording a thinner analysis
than a short one: 24 concepts is a good map of a four-minute sketch and 4.6 concepts an
hour on a five-hour interview. Budgeting per chunk keeps the density roughly constant,
so a 22-minute talk is one chunk and unchanged while five hours yields on the order of
sixty.
"""

CHUNK_TARGET_SECONDS = 1800.0
"""
Target audio duration per extraction call, before snapping to section boundaries.

Time sets the budget so the number of calls is proportional to length — about 11 for a
five-hour episode, 24 for twelve hours — while sections set the actual cut, so no chunk
begins or ends mid-topic.
"""

EXTRACTION_PROMPT = dedent("""
    You are given a transcript as numbered turns, each with a citation key (its start
    time in seconds) and a speaker. Extract the key concepts of the conversation.

    A concept is a topic, an entity, or a claim that the conversation actually
    discusses. Prefer a short list of load-bearing concepts over an
    exhaustive inventory; at most {max_concepts}.

    Return ONLY a JSON object of this exact shape:

    {{"concepts": [
      {{
        "id": "kebab-case-slug",
        "label": "Short display label",
        "kind": "topic|entity|claim",
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
      "claim", wording each gloss as what is asserted or decided and by whom.
    - Use each id once, and write every label in sentence case, so labels read the
      same whichever part of the recording they came from.
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


def _format_turns(units: Sequence[RawUnit]) -> str:
    lines: list[str] = []
    for unit in units:
        speaker = f"{unit.label}: " if unit.label else ""
        text = " ".join(unit.text.split())
        lines.append(f"[key={unit.key}] {speaker}{text}")
    return "\n".join(lines)


def plan_chunks(
    units: Sequence[RawUnit], target_seconds: float = CHUNK_TARGET_SECONDS
) -> list[list[RawUnit]]:
    """
    Group units into extraction chunks of about `target_seconds`, cut at section seams.

    A chunk closes once it has covered the target duration and the next unit starts a new
    section, so boundaries land where the sectioning pass already found a topic change.
    A section longer than the target becomes a chunk on its own rather than being split,
    since splitting a topic is what this exists to avoid. Anything shorter than the
    target is a single chunk, which is the previous whole-document behavior.
    """
    if not units:
        return []
    chunks: list[list[RawUnit]] = []
    current: list[RawUnit] = []
    for unit in units:
        starts_section = bool(current) and unit.section != current[-1].section
        covered = bool(current) and unit.start - current[0].start >= target_seconds
        if starts_section and covered:
            chunks.append(current)
            current = []
        current.append(unit)
    if current:
        chunks.append(current)
    return chunks


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
    for raw in raw_list[:MAX_CONCEPTS_PER_CHUNK]:
        if not isinstance(raw, dict):
            continue
        concept = cast(dict[str, Any], raw)
        concept_id = str(concept.get("id") or "").strip()
        if not concept_id or concept_id in seen_ids:
            log.warning("Skipping concept with missing or duplicate id: %r", concept_id)
            continue
        seen_ids.add(concept_id)
        kind = normalize_concept_kind(concept.get("kind"))
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
                "kind": kind,
                "gloss": str(concept.get("gloss") or ""),
                "mentions": mentions,
                "relations": relations,
                "research": concept.get("research"),
            }
        )
    return concepts


def _extract_chunk(
    units: Sequence[RawUnit], model: LLMName, web_search: bool
) -> list[dict[str, Any]]:
    from kash.llm_utils.llm_completion import llm_template_completion

    prompt = EXTRACTION_PROMPT.format(
        max_concepts=MAX_CONCEPTS_PER_CHUNK,
        research_field=RESEARCH_FIELD if web_search else "",
        research_rules=RESEARCH_RULES + "\n" if web_search else "",
        search_clause=" and web results you corroborate" if web_search else "",
        turns=_format_turns(units),
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
    return _parse_concepts(response)


def extract_chunks(
    chunks: Sequence[Sequence[RawUnit]], model: LLMName, web_search: bool
) -> list[list[dict[str, Any]]]:
    """
    Extract concepts from each chunk, tolerating a chunk that comes back unusable.

    Chunking multiplies the calls, so it multiplies the chance one of them returns
    something unparsable — on the first long-form run, one response in ten did. Losing
    half an hour of the map is much better than losing all of it, so a failed chunk is
    logged and skipped. Only a total failure is an error.
    """
    results: list[list[dict[str, Any]]] = []
    failed = 0
    for position, chunk in enumerate(chunks):
        try:
            results.append(_extract_chunk(chunk, model, web_search))
        except ApiResultError as error:
            failed += 1
            log.warning(
                "Concept extraction failed for chunk %d/%d at %.0f min, continuing: %s",
                position + 1,
                len(chunks),
                chunk[0].start / 60,
                error,
            )
    if chunks and failed == len(chunks):
        raise ApiResultError(f"Concept extraction failed for all {failed} chunk(s)")
    return results


def _identity(concept: dict[str, Any]) -> str:
    """Match on the id, falling back to the label, so the same idea merges across chunks."""
    key = str(concept.get("id") or "").strip().lower()
    if key:
        return key
    return " ".join(str(concept.get("label") or "").split()).lower()


def merge_concepts(per_chunk: Sequence[Sequence[dict[str, Any]]]) -> list[dict[str, Any]]:
    """
    Fold per-chunk concepts into one map, in timeline order.

    A long conversation returns to the same idea in several chunks, so a merged concept
    takes the union of its mentions and relations and the first non-empty gloss. The
    first chunk to name a concept fixes its label and kind, which makes the result
    independent of anything but chunk order.

    Relations are left as they are: a chunk can name a target it never saw, and that
    target may well exist in another chunk. The index resolves relations once over the
    merged set, which is why validation belongs after the merge and not before it.
    """
    merged: dict[str, dict[str, Any]] = {}
    for chunk in per_chunk:
        for concept in chunk:
            key = _identity(concept)
            if not key:
                continue
            existing = merged.get(key)
            if existing is None:
                merged[key] = {**concept, "mentions": list(concept.get("mentions") or [])}
                continue
            seen = set(existing["mentions"])
            for mention in concept.get("mentions") or []:
                if mention not in seen:
                    seen.add(mention)
                    existing["mentions"].append(mention)
            relations = cast(list[dict[str, Any]], existing.get("relations") or [])
            known = {(r.get("to"), r.get("type")) for r in relations}
            for relation in cast(list[dict[str, Any]], concept.get("relations") or []):
                if (relation.get("to"), relation.get("type")) not in known:
                    relations.append(relation)
            existing["relations"] = relations
            if not existing.get("gloss"):
                existing["gloss"] = concept.get("gloss") or ""
            if not existing.get("research"):
                existing["research"] = concept.get("research")
    return list(merged.values())


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
    if not item.body:
        raise InvalidInput(f"Item must have a body: {item}")
    units = scan_raw_units(item.body)
    if not units:
        log.warning("No citation-anchored turns found; skipping concept extraction")
        return item.derived_copy(type=ItemType.doc)

    chunks = plan_chunks(units)
    log.info(
        "Extracting concepts from %d chunk(s) covering %.0f min",
        len(chunks),
        (units[-1].start - units[0].start) / 60,
    )
    concepts = merge_concepts(extract_chunks(chunks, model, web_search))
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
                    "kind": "claim",
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
    assert concepts[0]["kind"] == "claim"
    assert concepts[1]["kind"] == "topic"


def test_format_turns_uses_citation_keys() -> None:
    body = (
        "**Alice:** Hello there.\n"
        '<span class="citation timestamp-link" data-src="r.yml" data-timestamp="1.00">'
        '<a href="https://example.com?t=1s">00:01</a></span>\n'
    )

    turns = _format_turns(scan_raw_units(body))

    assert turns == "[key=1.00] Alice: Hello there."


def _unit(start: float, section: int) -> RawUnit:
    return RawUnit(key=f"{start:.2f}", start=start, label="A", text="x", section=section)


def test_plan_chunks_cuts_at_section_seams_after_the_target() -> None:
    # Four sections of 20 minutes each, one unit per five minutes.
    units = [_unit(i * 300.0, i // 4) for i in range(16)]

    chunks = plan_chunks(units, target_seconds=1800.0)

    # A chunk closes only once it has covered 30 min AND a new section starts, so the
    # cuts land at 40 min and 80 min rather than mid-section at 30 min.
    assert [[u.start for u in c][0] for c in chunks] == [0.0, 2400.0]
    assert [len(c) for c in chunks] == [8, 8]
    # Every cut falls where the section changes.
    assert all(a[-1].section != b[0].section for a, b in zip(chunks, chunks[1:], strict=False))


def test_plan_chunks_keeps_short_media_whole() -> None:
    units = [_unit(i * 60.0, i // 5) for i in range(20)]  # 20 min over 4 sections

    assert len(plan_chunks(units, target_seconds=1800.0)) == 1
    assert plan_chunks([]) == []


def test_plan_chunks_does_not_split_an_over_long_section() -> None:
    units = [_unit(i * 300.0, 0) for i in range(20)]  # one 100-minute section

    chunks = plan_chunks(units, target_seconds=1800.0)

    assert len(chunks) == 1


def test_one_failed_chunk_does_not_lose_the_others() -> None:
    from unittest.mock import patch

    import pytest

    chunks = [[_unit(i * 1800.0, i)] for i in range(4)]
    calls: list[int] = []

    def flaky(_units: object, _model: object, _search: object) -> list[dict[str, Any]]:
        calls.append(len(calls))
        if len(calls) == 2:
            raise ApiResultError("unparsable")
        return [{"id": f"c{len(calls)}", "label": "L", "kind": "topic", "mentions": []}]

    with patch("deep_transcribe.concept_map._extract_chunk", side_effect=flaky):
        results = extract_chunks(chunks, LLM.default_structured, False)

    assert len(calls) == 4  # the failure did not stop the run
    assert len(results) == 3

    def always_fails(_units: object, _model: object, _search: object) -> list[dict[str, Any]]:
        raise ApiResultError("unparsable")

    with (
        patch("deep_transcribe.concept_map._extract_chunk", side_effect=always_fails),
        pytest.raises(ApiResultError, match="all 4"),
    ):
        extract_chunks(chunks, LLM.default_structured, False)


def test_merge_concepts_unions_mentions_and_keeps_first_label() -> None:
    first: list[dict[str, Any]] = [
        {
            "id": "agents",
            "label": "Agents",
            "kind": "topic",
            "gloss": "",
            "mentions": ["1.00", "2.00"],
            "relations": [{"to": "linux", "type": "leads-to"}],
            "research": None,
        }
    ]
    second: list[dict[str, Any]] = [
        {
            "id": "agents",
            "label": "Coding agents",
            "kind": "claim",
            "gloss": "Later gloss.",
            "mentions": ["2.00", "9000.00"],
            "relations": [
                {"to": "linux", "type": "leads-to"},
                {"to": "rust", "type": "example-of"},
            ],
            "research": None,
        },
        {"id": "rust", "label": "Rust", "kind": "entity", "gloss": "", "mentions": ["8000.00"]},
    ]

    merged = merge_concepts([first, second])

    assert [c["id"] for c in merged] == ["agents", "rust"]
    agents = merged[0]
    assert agents["label"] == "Agents"  # the first chunk to name it fixes the label
    assert agents["kind"] == "topic"
    assert agents["mentions"] == ["1.00", "2.00", "9000.00"]
    assert agents["gloss"] == "Later gloss."  # first non-empty wins
    assert len(cast(list[Any], agents["relations"])) == 2


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
