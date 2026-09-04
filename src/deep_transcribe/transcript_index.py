from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from kash.exec import kash_action, kash_precondition
from kash.exec.preconditions import has_simple_text_body, has_timestamps
from kash.model import Item
from kash.utils.errors import InvalidInput

INDEX_ELEMENT_ID = "dt-transcript-index"
"""DOM id of the embedded JSON transcript index."""

INDEX_VERSION = 1
"""Bump when the index JSON contract changes incompatibly."""

# Citations rendered by format_timestamp_citation: class first, then data attributes.
_CITATION_PATTERN = re.compile(
    r'<span class="citation timestamp-link"[^>]*\bdata-timestamp="(?P<ts>\d+(?:\.\d+)?)"'
    r"[^>]*>.*?</span>",
    re.DOTALL,
)
# Raw per-sentence spans from transcription, where data-timestamp is the only attribute.
# Citations never match: their spans always start with a class attribute.
_SENTENCE_SPAN_PATTERN = re.compile(r'<span data-timestamp="(?P<ts>\d+(?:\.\d+)?)">')
_H2_PATTERN = re.compile(r"^##(?!#)\s+(?P<heading>.+?)\s*$", re.MULTILINE)
_FRAME_PATTERN = re.compile(
    r'<img class="frame-capture" src="(?P<src>[^"]+)" alt="Frame at (?P<ts>\d+(?:\.\d+)?) seconds"'
    r"[^>]*>"
)
_SPEAKER_LABEL_PATTERN = re.compile(r"^\*\*(?P<name>[^*\n]{1,80}?):\*\*")
_DIV_LINE_PATTERN = re.compile(r"^\s*</?div[^>]*>\s*$", re.MULTILINE)
_TAG_PATTERN = re.compile(r"<[^>]+>")
_ISLAND_PATTERN = re.compile(
    r'\n*<script type="application/json" id="' + INDEX_ELEMENT_ID + r'">.*?</script>\n*',
    re.DOTALL,
)

_EXCERPT_MAX_CHARS = 140

CONCEPT_KINDS = frozenset({"topic", "entity", "claim"})
"""Closed vocabulary for concept kinds."""

CONCEPT_KIND_ALIASES = {"decision": "claim", "term": "topic"}
"""Retired kinds fold into the fixed ontology, so older extractions normalize."""


def normalize_concept_kind(kind: object) -> str:
    name = str(kind or "topic")
    name = CONCEPT_KIND_ALIASES.get(name, name)
    return name if name in CONCEPT_KINDS else "topic"


CONCEPT_RELATION_TYPES = frozenset(
    {"leads-to", "contrasts-with", "elaborates", "example-of", "depends-on"}
)
"""Closed vocabulary for concept relations, so the renderer has a fixed visual language."""


@dataclass(frozen=True)
class SpeakerEntry:
    id: str
    name: str
    order: int


@dataclass(frozen=True)
class SectionEntry:
    id: str
    heading: str
    start: float
    end: float


@dataclass(frozen=True)
class UnitEntry:
    uid: str
    key: str
    speaker: str | None
    section: str | None
    start: float
    end: float
    words: int
    sentences: int
    sentence_times: list[float]
    excerpt: str


@dataclass(frozen=True)
class FrameEntry:
    uid: str
    key: str | None
    t: float
    src: str


@dataclass(frozen=True)
class TranscriptIndex:
    media_url: str | None
    media_duration: float | None
    media_title: str | None
    has_video: bool
    speakers: list[SpeakerEntry]
    sections: list[SectionEntry]
    units: list[UnitEntry]
    frames: list[FrameEntry]
    concepts: list[dict[str, object]] = field(default_factory=list)

    def to_json_dict(self) -> dict[str, object]:
        by_speaker: dict[str, dict[str, float | int]] = {}
        for unit in self.units:
            if unit.speaker is None:
                continue
            totals = by_speaker.setdefault(
                unit.speaker, {"turns": 0, "words": 0, "sentences": 0, "seconds": 0.0}
            )
            totals["words"] += unit.words
            totals["sentences"] += unit.sentences
            totals["seconds"] = round(float(totals["seconds"]) + (unit.end - unit.start), 2)
        # A turn starts where the speaker changes; continuation paragraphs don't count.
        previous_speaker: str | None = None
        for unit in self.units:
            if unit.speaker is not None and unit.speaker != previous_speaker:
                by_speaker[unit.speaker]["turns"] += 1
            previous_speaker = unit.speaker
        total_seconds = round(self.units[-1].end - self.units[0].start, 2) if self.units else 0.0
        return {
            "version": INDEX_VERSION,
            "media": {
                "url": self.media_url,
                "duration": self.media_duration,
                "title": self.media_title,
                "has_video": self.has_video,
            },
            "speakers": [{"id": s.id, "name": s.name, "order": s.order} for s in self.speakers],
            "sections": [
                {"id": s.id, "heading": s.heading, "start": s.start, "end": s.end}
                for s in self.sections
            ],
            "units": [
                {
                    "uid": u.uid,
                    "key": u.key,
                    "speaker": u.speaker,
                    "section": u.section,
                    "start": u.start,
                    "end": u.end,
                    "words": u.words,
                    "sentences": u.sentences,
                    "sentence_times": u.sentence_times,
                    "excerpt": u.excerpt,
                }
                for u in self.units
            ],
            "frames": [{"uid": f.uid, "key": f.key, "t": f.t, "src": f.src} for f in self.frames],
            "totals": {
                "by_speaker": by_speaker,
                "words": sum(u.words for u in self.units),
                "seconds": total_seconds,
            },
            "concepts": self.concepts,
        }


def extract_sentence_onsets(raw_body: str) -> list[float]:
    """Collect per-sentence start times from a raw transcript with sentence spans."""
    onsets = [float(m.group("ts")) for m in _SENTENCE_SPAN_PATTERN.finditer(raw_body)]
    return sorted(set(onsets))


def _plain_text(markup: str) -> str:
    text = _TAG_PATTERN.sub(" ", markup)
    text = text.replace("**", "")
    return " ".join(text.split())


def _excerpt_of(text: str) -> str:
    if len(text) <= _EXCERPT_MAX_CHARS:
        return text
    cut = text.rfind(" ", 0, _EXCERPT_MAX_CHARS)
    if cut <= 0:
        cut = _EXCERPT_MAX_CHARS
    return text[:cut] + "…"


_SENTENCE_END_PATTERN = re.compile(r"[.!?…]+[\"')\]]*(?:\s|$)")


def _count_sentences_naive(text: str) -> int:
    """Punctuation-based fallback when no raw sentence timings are available."""
    if not text:
        return 0
    return len(_SENTENCE_END_PATTERN.findall(text)) or 1


@dataclass(frozen=True)
class RawUnit:
    """One citation-anchored paragraph as scanned from the document body."""

    key: str
    start: float
    label: str | None
    text: str


def scan_raw_units(body: str) -> list[RawUnit]:
    """Scan citation-anchored units with their full text, label stripped."""
    citations = list(_CITATION_PATTERN.finditer(body))
    headings = list(_H2_PATTERN.finditer(body))
    frames = list(_FRAME_PATTERN.finditer(body))
    raw_units: list[RawUnit] = []
    for i, citation in enumerate(citations):
        # A unit's text runs from the nearest structural boundary to its citation.
        boundary = 0
        if i > 0:
            boundary = citations[i - 1].end()
        for match_list in (headings, frames):
            for m in match_list:
                if m.end() <= citation.start():
                    boundary = max(boundary, m.end())
        for m in _DIV_LINE_PATTERN.finditer(body, boundary, citation.start()):
            boundary = max(boundary, m.end())
        text = body[boundary : citation.start()].strip()
        label: str | None = None
        label_match = _SPEAKER_LABEL_PATTERN.match(text)
        if label_match:
            label = label_match.group("name").strip()
            text = text[label_match.end() :].strip()
        raw_units.append(
            RawUnit(
                key=citation.group("ts"), start=float(citation.group("ts")), label=label, text=text
            )
        )
    return raw_units


def build_transcript_index(
    body: str,
    *,
    title: str | None = None,
    url: str | None = None,
    roster: list[str] | None = None,
    duration: float | None = None,
    sentence_onsets: list[float] | None = None,
    has_video: bool = False,
    concepts: list[dict[str, object]] | None = None,
) -> TranscriptIndex:
    """
    Build the transcript index from a formatted transcript body.

    Pure: consumes the final `md_html` body plus already-resolved metadata and returns
    the index. Citation spans are the join keys; the visible prose is never modified.
    """
    citations = list(_CITATION_PATTERN.finditer(body))
    headings = list(_H2_PATTERN.finditer(body))
    frames = list(_FRAME_PATTERN.finditer(body))
    onsets = sentence_onsets or []

    # Speaker ids follow roster order; labels found only in the body are appended.
    names: list[str] = list(roster or [])
    speaker_ids: dict[str, str] = {name: f"s{i}" for i, name in enumerate(names)}

    def speaker_id_for(name: str) -> str:
        if name not in speaker_ids:
            speaker_ids[name] = f"s{len(names)}"
            names.append(name)
        return speaker_ids[name]

    units: list[UnitEntry] = []
    raw_units = scan_raw_units(body)
    starts = [raw.start for raw in raw_units]
    previous_speaker: str | None = None
    for i, raw in enumerate(raw_units):
        citation = citations[i]
        raw_text = raw.text
        if raw.label is not None:
            speaker = speaker_id_for(raw.label)
        else:
            speaker = previous_speaker
        previous_speaker = speaker

        start = starts[i]
        if i + 1 < len(starts):
            end = starts[i + 1]
        elif duration is not None and duration >= start:
            end = duration
        else:
            prior = [starts[j + 1] - starts[j] for j in range(len(starts) - 1)]
            end = round(start + (sum(prior) / len(prior) if prior else 30.0), 2)

        section: str | None = None
        for h_index, h in enumerate(headings):
            if h.end() <= citation.start():
                section = f"sec{h_index}"

        text = _plain_text(raw_text)
        in_range = [t for t in onsets if start <= t < end]
        times = in_range if in_range and in_range[0] <= start else [start, *in_range]
        # Spoken-sentence onsets from the raw transcript are the authoritative
        # segmentation; punctuation counting is the fallback without them.
        sentences = len(in_range) if in_range else _count_sentences_naive(text)
        units.append(
            UnitEntry(
                uid=f"p{i}",
                key=citation.group("ts"),
                speaker=speaker,
                section=section,
                start=start,
                end=end,
                words=len(text.split()),
                sentences=sentences,
                sentence_times=times,
                excerpt=_excerpt_of(text),
            )
        )

    last_end = units[-1].end if units else 0.0
    sections: list[SectionEntry] = []
    for h_index, h in enumerate(headings):
        section_id = f"sec{h_index}"
        in_section = [u for u in units if u.section == section_id]
        start = in_section[0].start if in_section else last_end
        sections.append(
            SectionEntry(id=section_id, heading=h.group("heading"), start=start, end=start)
        )
    for h_index in range(len(sections)):
        end = sections[h_index + 1].start if h_index + 1 < len(sections) else last_end
        sections[h_index] = SectionEntry(
            id=sections[h_index].id,
            heading=sections[h_index].heading,
            start=sections[h_index].start,
            end=end,
        )

    frame_entries: list[FrameEntry] = []
    for f_index, frame in enumerate(frames):
        key: str | None = None
        for citation in citations:
            if citation.end() <= frame.start():
                key = citation.group("ts")
        frame_entries.append(
            FrameEntry(
                uid=f"f{f_index}",
                key=key,
                t=float(frame.group("ts")),
                src=frame.group("src"),
            )
        )

    reported_duration = duration if duration is not None and duration >= last_end - 0.5 else None
    resolved_concepts = _resolve_concepts(concepts or [], units)
    return TranscriptIndex(
        media_url=url,
        media_duration=reported_duration,
        media_title=title,
        has_video=has_video,
        speakers=[
            SpeakerEntry(id=speaker_ids[name], name=name, order=i) for i, name in enumerate(names)
        ],
        sections=sections,
        units=units,
        frames=frame_entries,
        concepts=resolved_concepts,
    )


MIN_MENTION_WORDS = 3
"""
A mention has to point at a unit that says something.

An extractor asked to cite where a concept comes up will sometimes land on the
acknowledgment that follows it — "Mhmm.", "Yeah.", "Right." A one-word unit cannot be
about anything, and one of them an hour away from the rest stretches the concept's span
across most of the recording: on a 5.3-hour interview, eight such mentions pushed six of
twenty-four concepts past 15% of the running time. Three words is the smallest bar that
clears those without touching real short answers ("I'd say mass immigration.").
"""


def _resolve_concepts(
    concepts: list[dict[str, object]], units: list[UnitEntry]
) -> list[dict[str, object]]:
    """
    Validate extracted concepts against the built units.

    Mentions must cite citation keys that exist; unresolvable mentions are dropped, and
    a concept with no valid mention is dropped entirely. Spans and speakers are derived
    here so the extractor never asserts timing the transcript does not support.
    """
    import logging

    log = logging.getLogger(__name__)
    unit_by_key = {u.key: u for u in units}
    known_ids = {str(c.get("id")) for c in concepts}
    resolved: list[dict[str, object]] = []
    for concept in concepts:
        raw_mentions = concept.get("mentions")
        keys = (
            [str(k) for k in cast("list[object]", raw_mentions)]
            if isinstance(raw_mentions, list)
            else []
        )
        mention_units = [unit_by_key[k] for k in keys if k in unit_by_key]
        dropped = len(keys) - len(mention_units)
        if dropped:
            log.warning(
                "Dropping %d unresolvable mention(s) for concept %r", dropped, concept.get("id")
            )
        if not mention_units:
            log.warning("Dropping concept %r: no valid mentions", concept.get("id"))
            continue
        substantive = [u for u in mention_units if u.words >= MIN_MENTION_WORDS]
        # Keep everything if a concept only ever lands on short units, rather than
        # losing the concept over a rule meant to trim its outliers.
        if substantive and len(substantive) < len(mention_units):
            log.info(
                "Dropping %d acknowledgment mention(s) for concept %r",
                len(mention_units) - len(substantive),
                concept.get("id"),
            )
            mention_units = substantive
        raw_relations = concept.get("relations")
        relation_dicts = [
            cast("dict[str, object]", r)
            for r in (
                cast("list[object]", raw_relations) if isinstance(raw_relations, list) else []
            )
            if isinstance(r, dict)
        ]
        relations = [
            {"to": str(r.get("to")), "type": str(r.get("type"))}
            for r in relation_dicts
            if str(r.get("to")) in known_ids
            and str(r.get("to")) != str(concept.get("id"))
            and str(r.get("type")) in CONCEPT_RELATION_TYPES
        ]
        speakers = sorted({u.speaker for u in mention_units if u.speaker is not None})
        resolved.append(
            {
                "id": str(concept.get("id")),
                "label": str(concept.get("label") or concept.get("id")),
                "kind": normalize_concept_kind(concept.get("kind")),
                "gloss": str(concept.get("gloss") or ""),
                "mentions": [{"t": u.start, "key": u.key} for u in mention_units],
                "span": [
                    min(u.start for u in mention_units),
                    max(u.end for u in mention_units),
                ],
                "speakers": speakers,
                "relations": relations,
                "research": concept.get("research"),
            }
        )
    return resolved


def index_to_json(index: TranscriptIndex) -> str:
    """Compact JSON, safe to embed in a script element and in normalized Markdown."""
    payload = json.dumps(index.to_json_dict(), separators=(",", ":"), ensure_ascii=False)
    # `</` could close the script element early; `<\/` is the same string in JSON.
    payload = payload.replace("</", "<\\/")
    # With compact separators every space sits inside a string literal. Encoding them
    # as \u0020 leaves no break points, so Markdown normalization on save cannot
    # line-wrap the island mid-string.
    return payload.replace(" ", "\\u0020")


def render_index_island(index: TranscriptIndex) -> str:
    """
    One-line JSON island for the document body.

    Kept to a single top-level line: CommonMark passes a top-level `<script>` block
    through verbatim, while nested or multi-line forms get escaped or mangled.
    """
    return (
        f'<script type="application/json" id="{INDEX_ELEMENT_ID}">{index_to_json(index)}</script>'
    )


def strip_index_island(body: str) -> str:
    """Remove a previously attached index so the action stays idempotent on reruns."""
    return _ISLAND_PATTERN.sub("\n\n", body).strip() + "\n"


@kash_precondition
def has_sentence_timestamp_spans(item: Item) -> bool:
    return bool(item.body and _SENTENCE_SPAN_PATTERN.search(item.body))


@kash_precondition
def has_transcript_index(item: Item) -> bool:
    return bool(item.body and item.body.find(f'id="{INDEX_ELEMENT_ID}"') != -1)


def _ffprobe_duration(media_path: Path) -> float | None:
    import subprocess

    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(media_path),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    return round(float(json.loads(result.stdout)["format"]["duration"]), 2)


def _find_cached_media(url: str | None, external_path: str | None) -> tuple[Path | None, bool]:
    """Look up already-cached media without ever triggering a download."""
    if external_path and Path(external_path).is_file():
        suffix = Path(external_path).suffix.lower()
        return Path(external_path), suffix in (".mp4", ".webm", ".mkv", ".mov")
    if url and url.startswith("file://"):
        local = Path(url.removeprefix("file://"))
        if local.is_file():
            return local, local.suffix.lower() in (".mp4", ".webm", ".mkv", ".mov")
    if not url:
        return None, False
    from importlib import import_module

    from kash.media_base.media_cache import SUFFIX_MP3, SUFFIX_MP4
    from kash.media_base.media_services import canonicalize_media_url
    from kash.media_base.media_tools import _media_cache  # pyright: ignore[reportPrivateUsage]
    from kash.utils.common.url import Url

    # Service canonicalization needs the extractor registry loaded.
    import_module("kash.kits.media.media_services")
    canonical = canonicalize_media_url(Url(url))
    key = str(canonical) if canonical else url
    audio = _media_cache.find(key, suffix=SUFFIX_MP3)
    video = _media_cache.find(key, suffix=SUFFIX_MP4)
    return audio or video, video is not None


def _resolve_media_duration(item: Item) -> tuple[float | None, bool]:
    """Best effort: probe already-cached source media with ffprobe. Never raises."""
    from kash.workspaces.source_items import find_upstream_resource

    try:
        resource = find_upstream_resource(item)
        media_path, has_video = _find_cached_media(resource.url, resource.external_path)
        if media_path is None:
            return None, has_video
        return _ffprobe_duration(media_path), has_video
    except Exception:
        return None, False


def _resolve_sentence_onsets(item: Item) -> list[float]:
    """Best effort: pull sentence start times from the raw timestamped transcript."""
    from kash.utils.errors import NoMatch
    from kash.workspaces.source_items import find_upstream_item

    try:
        source = find_upstream_item(item, has_sentence_timestamp_spans, include_self=False)
    except (NoMatch, ValueError):
        return []
    return extract_sentence_onsets(source.body or "")


@kash_action(precondition=has_simple_text_body & has_timestamps)
def attach_transcript_index(item: Item) -> Item:
    """
    Compute the transcript index and embed it in the document as a JSON island.

    The visible prose is untouched; the index binds to existing citation spans by
    their `data-timestamp` values.
    """
    from deep_transcribe.transcription_metadata import get_concepts, get_speaker_roster

    if not item.body:
        raise InvalidInput(f"Item must have a body: {item}")

    body = strip_index_island(item.body)
    duration, has_video = _resolve_media_duration(item)
    index = build_transcript_index(
        body,
        title=item.title,
        url=item.url,
        roster=get_speaker_roster(item),
        duration=duration,
        sentence_onsets=_resolve_sentence_onsets(item),
        has_video=has_video,
        concepts=get_concepts(item),
    )
    return item.derived_copy(body=f"{body.rstrip()}\n\n{render_index_island(index)}\n")


## Tests

_TEST_BODY = """<div class="description">

A synopsis paragraph that must not become a unit.

</div>

<div class="original">

## First Section

**Alice:** Hello there.
Welcome to the show.
<span class="citation timestamp-link" data-src="resources/x.resource.yml" data-timestamp="1.00"><a href="https://example.com?t=1s">00:01</a></span><img class="frame-capture" src="assets/f0.jpg" alt="Frame at 1.0 seconds" />

**Bob:** Thanks.
Glad to be here today.
<span class="citation timestamp-link" data-src="resources/x.resource.yml" data-timestamp="5.50"><a href="https://example.com?t=5.5s">00:05</a></span>

It is a long answer that continues in a second paragraph.
<span class="citation timestamp-link" data-src="resources/x.resource.yml" data-timestamp="9.00"><a href="https://example.com?t=9s">00:09</a></span>

## Second Section

**Alice:** Closing thoughts.
<span class="citation timestamp-link" data-src="resources/x.resource.yml" data-timestamp="12.00"><a href="https://example.com?t=12s">00:12</a></span>

</div>
"""


def test_build_index_units_speakers_and_sections() -> None:
    index = build_transcript_index(
        _TEST_BODY,
        title="Test",
        url="https://example.com",
        roster=["Alice", "Bob"],
        duration=20.0,
        sentence_onsets=[1.0, 2.2, 5.5, 6.4, 9.0, 12.0],
        has_video=True,
    )

    assert [s.name for s in index.speakers] == ["Alice", "Bob"]
    assert [u.key for u in index.units] == ["1.00", "5.50", "9.00", "12.00"]
    assert [u.speaker for u in index.units] == ["s0", "s1", "s1", "s0"]
    assert [u.section for u in index.units] == ["sec0", "sec0", "sec0", "sec1"]
    assert [u.start for u in index.units] == [1.0, 5.5, 9.0, 12.0]
    assert [u.end for u in index.units] == [5.5, 9.0, 12.0, 20.0]
    assert index.units[0].sentence_times == [1.0, 2.2]
    assert index.units[0].sentences == 2
    assert index.units[0].words == 6
    assert "Hello there." in index.units[0].excerpt
    # The synopsis and the frame img must not leak into any unit's text.
    assert all("synopsis" not in u.excerpt for u in index.units)
    assert all("img" not in u.excerpt for u in index.units)

    assert [s.heading for s in index.sections] == ["First Section", "Second Section"]
    assert index.sections[0].start == 1.0
    assert index.sections[0].end == 12.0
    assert index.sections[1].end == 20.0

    assert len(index.frames) == 1
    assert index.frames[0].key == "1.00"
    assert index.frames[0].t == 1.0

    totals = index.to_json_dict()["totals"]
    assert isinstance(totals, dict)
    assert totals["by_speaker"]["s1"]["turns"] == 1  # continuation isn't a new turn
    assert totals["by_speaker"]["s0"]["turns"] == 2
    assert totals["seconds"] == 19.0


def test_build_index_without_duration_estimates_tail() -> None:
    index = build_transcript_index(_TEST_BODY, roster=["Alice", "Bob"], duration=None)

    mean_gap = ((5.5 - 1.0) + (9.0 - 5.5) + (12.0 - 9.0)) / 3
    assert index.media_duration is None
    assert index.units[-1].end == round(12.0 + mean_gap, 2)


def test_build_index_appends_unknown_labels_to_roster() -> None:
    index = build_transcript_index(_TEST_BODY, roster=["Alice"])

    assert [s.name for s in index.speakers] == ["Alice", "Bob"]
    assert index.speakers[1].id == "s1"


def test_acknowledgment_mentions_do_not_stretch_a_span() -> None:
    def unit(key: str, start: float, end: float, words: int) -> UnitEntry:
        return UnitEntry(
            uid=f"p{key}",
            key=key,
            speaker="s0",
            section="sec0",
            start=start,
            end=end,
            words=words,
            sentences=1,
            sentence_times=[start],
            excerpt="",
        )

    units = [
        unit("1.00", 1.0, 40.0, 90),
        unit("50.00", 50.0, 90.0, 80),
        unit("9000.00", 9000.0, 9002.0, 1),  # "Mhmm." an hour later
    ]
    concept: dict[str, object] = {
        "id": "c1",
        "label": "A concept",
        "kind": "topic",
        "mentions": ["1.00", "50.00", "9000.00"],
    }

    [resolved] = _resolve_concepts([concept], units)

    assert [m["key"] for m in cast("list[dict[str, object]]", resolved["mentions"])] == [
        "1.00",
        "50.00",
    ]
    assert resolved["span"] == [1.0, 90.0]


def test_a_concept_of_only_short_mentions_keeps_them() -> None:
    units = [
        UnitEntry(
            uid="p1",
            key="1.00",
            speaker="s0",
            section=None,
            start=1.0,
            end=3.0,
            words=2,
            sentences=1,
            sentence_times=[1.0],
            excerpt="",
        )
    ]
    concept: dict[str, object] = {
        "id": "c1",
        "label": "Terse",
        "kind": "topic",
        "mentions": ["1.00"],
    }

    [resolved] = _resolve_concepts([concept], units)

    assert len(cast("list[object]", resolved["mentions"])) == 1


def test_extract_sentence_onsets_ignores_citations() -> None:
    raw = (
        '<span data-timestamp="1.00">Hi.</span> <span data-timestamp="2.50">There.</span> '
        '<span class="citation timestamp-link" data-timestamp="99.0">00:09</span>'
    )

    assert extract_sentence_onsets(raw) == [1.0, 2.5]


def test_index_island_roundtrip_and_escaping() -> None:
    index = build_transcript_index(_TEST_BODY, roster=["Alice", "Bob"], duration=20.0)
    island = render_index_island(index)

    assert island.startswith('<script type="application/json"')
    assert "</p" not in island.split("</script>")[0].replace("<\\/", "")
    parsed = json.loads(island.split(">", 1)[1].rsplit("</script>", 1)[0])
    assert parsed["version"] == INDEX_VERSION
    assert len(parsed["units"]) == 4

    body_with_island = f"{_TEST_BODY}\n\n{island}\n"
    assert strip_index_island(body_with_island).strip() == _TEST_BODY.strip()


def test_minify_preserves_json_island(tmp_path: Path) -> None:
    """The published page must keep the index parseable after minification."""
    import shutil
    import subprocess

    import pytest

    if shutil.which("npx") is None:
        pytest.skip("npx not available")
    from tminify.main import get_js_dir

    index = build_transcript_index(_TEST_BODY, roster=["Alice", "Bob"], duration=20.0)
    island = render_index_island(index)
    src = tmp_path / "page.html"
    src.write_text(
        f"<!DOCTYPE html><html><head><title>t</title></head><body>{island}</body></html>"
    )
    result = subprocess.run(
        [
            "npx",
            "html-minifier-terser",
            "--collapse-whitespace",
            "--remove-comments",
            "--minify-css",
            "true",
            "--minify-js",
            "true",
            str(src),
        ],
        cwd=get_js_dir(),
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    match = re.search(f'id="{INDEX_ELEMENT_ID}">(.*?)</script>', result.stdout, re.DOTALL)
    assert match
    assert json.loads(match.group(1)) == index.to_json_dict()
