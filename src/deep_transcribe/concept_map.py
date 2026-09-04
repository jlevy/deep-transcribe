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

from deep_transcribe.chunking import plan_chunks
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

    Chunking multiplies the calls, so it multiplies the chance one of them fails — on the
    first long-form run one response in ten came back unparsable, and a later run hit a
    provider timeout after ten minutes. Losing half an hour of the map is much better
    than losing all of it, so a failed chunk is logged and skipped whatever the cause.
    Only a total failure is an error.
    """
    results: list[list[dict[str, Any]]] = []
    failed = 0
    for position, chunk in enumerate(chunks):
        try:
            results.append(_extract_chunk(chunk, model, web_search))
        except Exception as error:
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


REDUCE_THRESHOLD = 2
"""
Chunk count above which the reduce pass runs.

A single-chunk recording has nothing to reconcile: its concepts came from one call that
already saw them together. Running the pass anyway would spend a call to reorganize a
list that is short enough to read as-is, and would change output for short media that is
working.
"""

REDUCE_PROMPT = dedent("""
    You are given the concept map of one long recording, extracted in pieces from
    consecutive stretches of the conversation and then concatenated. Because each piece
    was extracted without seeing the others, the list has three problems, and your job
    is to fix exactly those three and change nothing else.

    1. DUPLICATES. The same idea appears more than once under different labels, because
       adjacent stretches both covered it. Merge these freely — this is the one place
       where you should act on a reasonable suspicion rather than wait for certainty,
       because two entries for one idea is a worse map than one entry with a slightly
       broad label. Keep the id whose label reads best and list the others as merged
       into it.

       Two entries are the same idea when a reader would be surprised to find them
       listed separately. Watch for: the same thing named once in general and once by a
       specific instance; a topic and a claim about that topic; the same argument made
       with different words in two neighbouring stretches; and the same named product,
       person, or paper spelled inconsistently, since a transcript renders hard proper
       nouns differently each time it hears them. Genuinely distinct claims about one
       subject are NOT duplicates and stay separate.

    2. NO STRUCTURE. A flat list of this many concepts is not a map of anything. Group
       every concept you keep under a theme — a short noun phrase naming a strand the
       conversation actually follows. Aim for 6 to 12 themes over the whole recording,
       each holding a handful of concepts. Order themes as the conversation reaches
       them; order concepts within a theme the same way.

    3. MINOR ENTRIES. Some concepts looked worth naming inside one stretch and do not
       hold up against the whole conversation — a passing example, an aside. Drop those.
       Here, and only here, be conservative: dropping a real strand of the conversation
       is much worse than keeping a thin one, and anything that is the only concept
       covering its part of the recording stays. Caution about dropping says nothing
       about merging, which you should do freely.

    Return ONLY a JSON object of this exact shape:

    {{"themes": [
      {{"label": "Short theme name", "concepts": ["concept-id", "concept-id"]}}
    ],
    "merges": [{{"keep": "concept-id", "merged": ["concept-id", "concept-id"]}}],
    "dropped": ["concept-id"]}}

    Rules:
    - Every id you write MUST be one of the ids listed below, copied exactly. Do not
      invent ids and do not invent concepts.
    - Every kept concept appears under exactly one theme. A merged or dropped id must
      not appear under any theme.
    - Do not rewrite labels or glosses. You are organizing, not rewriting.

    Concepts, in the order the conversation reaches them:

    {concepts}
    """).strip()


def _format_concepts_for_reduce(concepts: Sequence[dict[str, Any]]) -> str:
    lines: list[str] = []
    for concept in concepts:
        gloss = " ".join(str(concept.get("gloss") or "").split())
        lines.append(f"- {concept['id']} [{concept.get('kind')}] {concept.get('label')} — {gloss}")
    return "\n".join(lines)


def _parse_reduce(
    response: str, known: set[str]
) -> tuple[list[tuple[str, list[str]]], dict[str, str], set[str]]:
    """
    Parse a reduce response into (themes, merged-into, dropped), keeping only known ids.

    The model is organizing a list it was handed, so anything it names that was not on
    that list is a mistake rather than an addition, and is discarded here.
    """
    parsed = fuzzy_parse_json(response)
    if not isinstance(parsed, dict):
        raise ApiResultError(f"Reduce response is not a JSON object: {response[:200]}")
    payload = cast(dict[str, Any], parsed)

    merged_into: dict[str, str] = {}
    for raw in cast(list[object], payload.get("merges") or []):
        if not isinstance(raw, dict):
            continue
        merge = cast(dict[str, Any], raw)
        keep = str(merge.get("keep") or "")
        if keep not in known:
            continue
        for other in cast(list[object], merge.get("merged") or []):
            other_id = str(other)
            if other_id in known and other_id != keep:
                merged_into[other_id] = keep

    dropped = {str(d) for d in cast(list[object], payload.get("dropped") or [])} & known
    dropped -= set(merged_into.values())

    themes: list[tuple[str, list[str]]] = []
    for raw in cast(list[object], payload.get("themes") or []):
        if not isinstance(raw, dict):
            continue
        theme = cast(dict[str, Any], raw)
        label = " ".join(str(theme.get("label") or "").split())
        members = [
            str(c)
            for c in cast(list[object], theme.get("concepts") or [])
            if str(c) in known and str(c) not in merged_into and str(c) not in dropped
        ]
        if label and members:
            themes.append((label, members))
    return themes, merged_into, dropped


def _mention_seconds(key: str) -> float:
    """Citation keys are start times in seconds; an unparsable one sorts last."""
    try:
        return float(key)
    except ValueError:
        return float("inf")


def apply_reduction(
    concepts: Sequence[dict[str, Any]],
    themes: Sequence[tuple[str, list[str]]],
    merged_into: dict[str, str],
    dropped: set[str],
) -> list[dict[str, Any]]:
    """
    Rewrite the concept list from a reduce result, in theme order.

    Merging folds mentions and relations into the surviving concept, so nothing the
    transcript actually supports is lost when two labels turn out to name one idea.
    A concept the model failed to place keeps its place rather than disappearing: an
    unthemed leftover is a smaller problem than a silently missing concept.
    """
    by_id = {str(c["id"]): c for c in concepts}
    for source, target in merged_into.items():
        loser, winner = by_id.get(source), by_id.get(target)
        if not loser or not winner:
            continue
        seen = set(cast(list[str], winner.get("mentions") or []))
        for mention in cast(list[str], loser.get("mentions") or []):
            if mention not in seen:
                seen.add(mention)
                cast(list[str], winner["mentions"]).append(mention)
        relations = cast(list[dict[str, Any]], winner.get("relations") or [])
        known = {(r.get("to"), r.get("type")) for r in relations}
        for relation in cast(list[dict[str, Any]], loser.get("relations") or []):
            if (relation.get("to"), relation.get("type")) not in known:
                relations.append(relation)
        winner["relations"] = relations
        if not winner.get("gloss"):
            winner["gloss"] = loser.get("gloss") or ""

    removed = set(merged_into) | dropped

    def first_mention(concept: dict[str, Any]) -> float:
        times = [_mention_seconds(m) for m in cast(list[str], concept.get("mentions") or [])]
        return min(times) if times else float("inf")

    # Order by the clock rather than by what the model returned. Themes are asked for in
    # the order the conversation reaches them and do not always come back that way, and
    # this is a fact the mentions already settle.
    placed: set[str] = set()
    groups: list[tuple[float, str, list[dict[str, Any]]]] = []
    for label, members in themes:
        members_kept: list[dict[str, Any]] = []
        for concept_id in members:
            concept = by_id.get(concept_id)
            if concept is None or concept_id in removed or concept_id in placed:
                continue
            placed.add(concept_id)
            members_kept.append({**concept, "theme": label})
        if members_kept:
            members_kept.sort(key=first_mention)
            groups.append((first_mention(members_kept[0]), label, members_kept))
    groups.sort(key=lambda g: g[0])

    ordered: list[dict[str, Any]] = [c for _, _, members in groups for c in members]
    # A concept no theme claimed keeps its place at the end rather than disappearing.
    for concept in concepts:
        concept_id = str(concept["id"])
        if concept_id in removed or concept_id in placed:
            continue
        ordered.append({**concept, "theme": None})
    return ordered


def reduce_concepts(concepts: Sequence[dict[str, Any]], model: LLMName) -> list[dict[str, Any]]:
    """
    Organize a merged concept map: collapse duplicates, group into themes, drop the minor.

    This is the step chunking makes possible. The transcript is 55,000 words but its
    concept map with glosses is a few thousand, so one call can hold the whole thing and
    make judgments no single chunk could — that two labels name one idea, that a strand
    runs through the conversation, that an entry looked bigger from inside its half hour
    than it does from outside. Extraction is local where the detail is; this is global
    where the overview is.

    A failure here returns the input unchanged. An unorganized map is still a map.
    """
    from kash.llm_utils.llm_completion import llm_template_completion

    prompt = REDUCE_PROMPT.format(concepts=_format_concepts_for_reduce(concepts))
    escaped_prompt = prompt.replace("{", "{{").replace("}", "}}")
    try:
        response = llm_template_completion(
            model=model,
            system_message=Message(
                "You organize an already-extracted concept map. You never add, rename, "
                "or reword anything."
            ),
            input="Organize the supplied concept map.",
            body_template=MessageTemplate(escaped_prompt + "\n\n{body}"),
        ).content
        themes, merged_into, dropped = _parse_reduce(response, {str(c["id"]) for c in concepts})
    except Exception as error:
        # Deliberately broad. This pass is pure improvement over a map that already
        # exists, so nothing it can raise is worth losing that map for — and the first
        # real failure was a provider timeout, which is not an ApiResultError and would
        # have thrown away ten successful chunk extractions on its way out.
        log.warning("Concept reduce pass failed, keeping the unorganized map: %s", error)
        return list(concepts)

    reduced = apply_reduction(concepts, themes, merged_into, dropped)
    log.info(
        "Reduced %d concepts to %d in %d themes (%d merged, %d dropped)",
        len(concepts),
        len(reduced),
        len(themes),
        len(merged_into),
        len(dropped),
    )
    return reduced


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
    if len(chunks) >= REDUCE_THRESHOLD:
        concepts = reduce_concepts(concepts, model)
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


def _concept(concept_id: str, mentions: list[str]) -> dict[str, Any]:
    return {
        "id": concept_id,
        "label": concept_id.replace("-", " ").capitalize(),
        "kind": "topic",
        "gloss": "",
        "mentions": mentions,
        "relations": [],
        "research": None,
    }


def test_a_timeout_in_the_reduce_pass_keeps_the_map() -> None:
    from unittest.mock import patch

    concepts = [_concept("a", ["1.00"]), _concept("b", ["2.00"])]

    # A provider timeout is not an ApiResultError, and losing an extracted map to one
    # would throw away every chunk call that already succeeded.
    with patch(
        "kash.llm_utils.llm_completion.llm_template_completion",
        side_effect=TimeoutError("Connection timed out after 600.0 seconds"),
    ):
        assert reduce_concepts(concepts, LLM.default_structured) == concepts


def test_a_timeout_in_one_chunk_does_not_lose_the_others() -> None:
    from unittest.mock import patch

    chunks = [[_unit(i * 1800.0, i)] for i in range(3)]
    calls: list[int] = []

    def flaky(_units: object, _model: object, _search: object) -> list[dict[str, Any]]:
        calls.append(len(calls))
        if len(calls) == 1:
            raise TimeoutError("Connection timed out after 600.0 seconds")
        return [{"id": f"c{len(calls)}", "label": "L", "kind": "topic", "mentions": []}]

    with patch("deep_transcribe.concept_map._extract_chunk", side_effect=flaky):
        results = extract_chunks(chunks, LLM.default_structured, False)

    assert len(calls) == 3
    assert len(results) == 2


def test_reduce_merges_folds_mentions_and_orders_by_theme() -> None:
    concepts = [
        _concept("agents", ["1.00"]),
        _concept("coding-agents", ["2.00"]),
        _concept("linux", ["3.00"]),
        _concept("passing-aside", ["4.00"]),
    ]
    response = json.dumps(
        {
            "themes": [
                {"label": "Operating systems", "concepts": ["linux"]},
                {"label": "Agentic coding", "concepts": ["agents"]},
            ],
            "merges": [{"keep": "agents", "merged": ["coding-agents"]}],
            "dropped": ["passing-aside"],
        }
    )

    themes, merged_into, dropped = _parse_reduce(response, {str(c["id"]) for c in concepts})
    reduced = apply_reduction(concepts, themes, merged_into, dropped)

    # The model listed Operating systems first, but agents is mentioned earlier, and the
    # clock decides.
    assert [c["id"] for c in reduced] == ["agents", "linux"]
    assert [c["theme"] for c in reduced] == ["Agentic coding", "Operating systems"]
    assert reduced[0]["mentions"] == ["1.00", "2.00"]  # the merged concept's mentions survive


def test_reduce_orders_themes_and_members_by_the_clock() -> None:
    concepts = [
        _concept("late", ["9000.00"]),
        _concept("early", ["10.00"]),
        _concept("middle", ["4000.00"]),
    ]
    # The model returns the later theme first and its members out of order.
    themes = [("Second half", ["late", "middle"]), ("Opening", ["early"])]

    reduced = apply_reduction(concepts, themes, {}, set())

    assert [c["theme"] for c in reduced] == ["Opening", "Second half", "Second half"]
    assert [c["id"] for c in reduced] == ["early", "middle", "late"]


def test_reduce_ignores_ids_it_was_never_given() -> None:
    response = json.dumps(
        {
            "themes": [{"label": "T", "concepts": ["real", "invented"]}],
            "merges": [{"keep": "invented", "merged": ["real"]}],
            "dropped": ["also-invented"],
        }
    )

    themes, merged_into, dropped = _parse_reduce(response, {"real"})

    assert themes == [("T", ["real"])]
    assert merged_into == {}  # a merge into an id that does not exist is discarded
    assert dropped == set()


def test_reduce_keeps_a_concept_no_theme_claimed() -> None:
    concepts = [_concept("named", ["1.00"]), _concept("forgotten", ["2.00"])]

    reduced = apply_reduction(concepts, [("T", ["named"])], {}, set())

    assert [c["id"] for c in reduced] == ["named", "forgotten"]
    assert reduced[1]["theme"] is None


def test_reduce_failure_returns_the_map_unchanged() -> None:
    from unittest.mock import patch

    concepts = [_concept("a", ["1.00"]), _concept("b", ["2.00"])]

    with patch(
        "kash.llm_utils.llm_completion.llm_template_completion",
        side_effect=ApiResultError("no"),
    ):
        assert reduce_concepts(concepts, LLM.default_structured) == concepts


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
