"""
What a run produced, read off the final item so an agent can decide what to change next.

The loop this tool is built around is run, look at the result, adjust an input, rerun.
Looking at the result used to mean a browser or a one-off script over the item YAML, which
is why every correction made on the five-hour recording during stabilization was found by
hand. This is that look, as text or JSON: the counts and lists that say whether the
sections are too fine, which stretches were set aside, and which names the transcriber
spelled more than one way.

Everything here comes from the final item — its body and its `extra` — and nothing from
the exported HTML. The page is a rendering of this item, so counting it instead would
measure the template.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from deep_transcribe.segment_hints import format_time

if TYPE_CHECKING:
    from kash.model import Item

log = logging.getLogger(__name__)

HEADING_LIST_LIMIT = 30
"""Above this many headings, show the first and last few and say how many were skipped."""

HEADING_LIST_EDGE = 5
"""How many headings to show at each end when the list is elided."""

SPELLING_LIMIT = 40
"""How many capitalized tokens to report. Enough to see the variants of a few names."""

MIN_SPELLING_LENGTH = 4
"""Shorter capitalized tokens are initials and interjections, not names worth a key term."""

_OUTLINE_REGION = re.compile(
    r'<div class="transcript-outline"[^>]*>(?P<outline>.*?)<div class="original">',
    re.DOTALL,
)
_OUTLINE_ENTRY = re.compile(r"^[-*+]\s+\*\*", re.MULTILINE)
_FRAME_TAG = '<img class="frame-capture"'
_WORDISH = re.compile(r"[A-Za-z][A-Za-z'’]*")
_MARKUP = re.compile(r"<[^>]+>")

ORDINARY_WORDS = frozenset(
    """
    about absolutely actually after again against almost alright already also although
    always among another anybody anymore anything anyway around because been before being
    believe better between both called cannot come could course definitely does doing done
    down during each either else enough especially even ever every everybody everyone
    everything exactly fine first from getting going gonna gotta great guess have having
    here hmm honestly huge imagine important instead interesting into itself just keep kind
    know last later less like little look looking lots made make making many maybe mean
    means might mhm mhmm more most much must myself need never next nice none nothing
    obviously often okay once only other others over part people perfect perhaps
    personally please pretty probably quite rather really remember right said same says
    seems several should similar simply since some somebody somehow someone something
    sometimes somewhere sorry still stuff such sure take taking talking tell than thank
    thanks that their them then there these they thing things think this those though
    thought through time today together totally true trying under understand until upon
    used using very want welcome well went were what whatever when where whether which
    while whole will with within without would wow yeah year years yep yes your yourself
    """.split()
)
"""
Ordinary English words and transcript back-channels that start a sentence and so get
capitalized. Not a language model, just the words that would otherwise crowd out the
proper nouns; deliberately free of anything about a particular recording's subject.
"""


@dataclass(frozen=True)
class HeadingEntry:
    """One `##` section heading and where the transcript first cites time under it."""

    title: str
    start: float | None


@dataclass(frozen=True)
class ThemeEntry:
    name: str
    concepts: int


@dataclass(frozen=True)
class SegmentEntry:
    """One hint in effect, with how much of the transcript it actually covers."""

    purpose: str
    start: float
    end: float
    suppressed: bool
    units: int


@dataclass(frozen=True)
class SpeakerEntry:
    label: str
    turns: int


@dataclass(frozen=True)
class SpellingEntry:
    token: str
    count: int


@dataclass(frozen=True)
class TranscriptReport:
    """The whole answer to "what did that run produce?", in a form both outputs render."""

    duration: float | None
    headings: list[HeadingEntry]
    outline_entries: int
    themes: list[ThemeEntry]
    unthemed_concepts: int
    segments: list[SegmentEntry]
    speakers: list[SpeakerEntry]
    frames_kept: int
    frames_captured: int | None
    spellings: list[SpellingEntry]

    @property
    def headings_per_hour(self) -> float | None:
        """Heading density, which is the number that says whether sections are too fine."""
        if not self.duration:
            return None
        return round(len(self.headings) * 3600.0 / self.duration, 1)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "duration": self.duration,
            "headings": {
                "count": len(self.headings),
                "per_hour": self.headings_per_hour,
                "list": [{"title": h.title, "start": h.start} for h in self.headings],
            },
            "outline": {"entries": self.outline_entries},
            "themes": {
                "count": len(self.themes),
                "unthemed_concepts": self.unthemed_concepts,
                "list": [{"name": t.name, "concepts": t.concepts} for t in self.themes],
            },
            "segments": [
                {
                    "purpose": s.purpose,
                    "at": f"{format_time(s.start)} - {format_time(s.end)}",
                    "start": s.start,
                    "end": s.end,
                    "suppressed": s.suppressed,
                    "units": s.units,
                }
                for s in self.segments
            ],
            "speakers": [{"label": s.label, "turns": s.turns} for s in self.speakers],
            "frames": {"kept": self.frames_kept, "captured": self.frames_captured},
            "spellings": [{"token": s.token, "count": s.count} for s in self.spellings],
        }


def _source_duration(item: Item) -> float | None:
    """
    Recording length in seconds, for the densities.

    The extractor's duration is copied down the pipeline with the rest of the source
    metadata, so the final item normally has it; the upstream resource is the fallback for
    an item that lost it, and a source no media service claims has none at all.
    """
    from deep_transcribe.disk_space import source_duration

    duration = source_duration(item)
    if duration is not None:
        return duration
    try:
        from kash.workspaces.source_items import find_upstream_resource

        return source_duration(find_upstream_resource(item))
    except Exception:
        return None


def _outline_entry_count(body: str) -> int:
    """
    Top-level bullets in the outline block, which is where `add_transcript_outline` puts it.

    Counted inside the block rather than over the whole body: the transcript prose can hold
    bold list items of its own, and the point of this number is how many sections the
    outline claims.
    """
    match = _OUTLINE_REGION.search(body)
    if not match:
        return 0
    return len(_OUTLINE_ENTRY.findall(match.group("outline")))


def _heading_entries(body: str, unit_starts_by_section: dict[int, float]) -> list[HeadingEntry]:
    from deep_transcribe.transcript_index import scan_section_headings

    return [
        HeadingEntry(title=title, start=unit_starts_by_section.get(index))
        for index, title in enumerate(scan_section_headings(body))
    ]


def _theme_entries(concepts: list[dict[str, Any]]) -> tuple[list[ThemeEntry], int]:
    counts: Counter[str] = Counter()
    unthemed = 0
    for concept in concepts:
        theme = concept.get("theme")
        name = str(theme).strip() if theme is not None else ""
        if name:
            counts[name] += 1
        else:
            unthemed += 1
    entries = [ThemeEntry(name=name, concepts=n) for name, n in counts.most_common()]
    return sorted(entries, key=lambda t: (-t.concepts, t.name)), unthemed


def _visible_text(markup: str) -> str:
    """Prose with tags and bold markers dropped, so tokens are words rather than markup."""
    return _MARKUP.sub(" ", markup).replace("**", " ")


def spelling_variants(texts: list[str], limit: int = SPELLING_LIMIT) -> list[SpellingEntry]:
    """
    The most frequent capitalized words, so a reader can spot one name spelled several ways.

    On the measured recording Omarchy came back as Omachi, Amache, Umaci and Umachi, about
    sixty times between them, and there was no way to see that short of reading five hours
    of transcript. Ranked by frequency because a name said often enough to matter is a name
    worth passing to `--key-term`; contractions are dropped because a word with an
    apostrophe is never the one you would pass.
    """
    counts: Counter[str] = Counter()
    for text in texts:
        for token in _WORDISH.findall(text):
            if "'" in token or "’" in token:
                continue
            if len(token) < MIN_SPELLING_LENGTH or not token[0].isupper():
                continue
            if token.lower() in ORDINARY_WORDS:
                continue
            counts[token] += 1
    return [
        SpellingEntry(token=token, count=n)
        for token, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
    ]


def build_transcript_report(item: Item) -> TranscriptReport:
    """
    Read the final item and answer what the run produced.

    Pure with respect to the pipeline: nothing is rerun and nothing is written. The only
    thing it may reach outside the item for is the source duration, and only to put the
    heading count on a per-hour footing.
    """
    from deep_transcribe.segment_hints import SegmentHints, parse_hints
    from deep_transcribe.transcript_index import scan_raw_units
    from deep_transcribe.transcription_metadata import get_concepts, get_segment_hints

    body = item.body or ""
    units = scan_raw_units(body)

    # The first unit under a heading is where that section starts; units carry the index of
    # the heading they fall under, and -1 before the first one.
    first_start_by_section: dict[int, float] = {}
    for unit in units:
        first_start_by_section.setdefault(unit.section, unit.start)

    try:
        hints = parse_hints(get_segment_hints(item))
    except ValueError as error:
        # A report must still report. Stored hints have already been through the run that
        # produced this item, so this is a stale or hand-edited file, not a fresh mistake.
        log.warning("Cannot read the segment hints on this item: %s", error)
        hints = SegmentHints()

    themes, unthemed = _theme_entries(get_concepts(item))
    speaker_counts = Counter(unit.label for unit in units if unit.label)

    return TranscriptReport(
        duration=_source_duration(item),
        headings=_heading_entries(body, first_start_by_section),
        outline_entries=_outline_entry_count(body),
        themes=themes,
        unthemed_concepts=unthemed,
        segments=[
            SegmentEntry(
                purpose=hint.purpose.value,
                start=hint.start,
                end=hint.end,
                suppressed=hint.suppressed,
                units=sum(1 for unit in units if hint.covers(unit.start)),
            )
            for hint in hints.segments
        ],
        speakers=[
            SpeakerEntry(label=label, turns=n)
            for label, n in sorted(speaker_counts.items(), key=lambda kv: (-kv[1], kv[0]))
        ],
        frames_kept=body.count(_FRAME_TAG),
        # `_thin_frame_captures` deletes the frames it drops and rewrites the same item, so
        # the pre-thinning count survives only in the run's log. Nothing on the item can
        # recover it, and a guess here would be read as a measurement.
        frames_captured=None,
        spellings=spelling_variants([_visible_text(unit.text) for unit in units]),
    )


def _heading_lines(report: TranscriptReport) -> list[str]:
    def line(entry: HeadingEntry) -> str:
        at = format_time(entry.start) if entry.start is not None else "-"
        return f"  {at:>9}  {entry.title}"

    headings = report.headings
    if len(headings) <= HEADING_LIST_LIMIT:
        return [line(entry) for entry in headings]
    head = headings[:HEADING_LIST_EDGE]
    tail = headings[-HEADING_LIST_EDGE:]
    skipped = len(headings) - len(head) - len(tail)
    return [
        *[line(entry) for entry in head],
        f"  … {skipped} more",
        *[line(entry) for entry in tail],
    ]


def format_report_text(report: TranscriptReport) -> str:
    """
    One section per field, no prose. Written to be read by an agent and skimmed by a person.

    Stays inside about 120 lines on a five-hour recording, which is what makes it safe to
    print after every run: the heading list elides its middle and the spellings are capped.
    """
    lines: list[str] = ["report"]

    duration = f"duration {format_time(report.duration)}" if report.duration else "duration -"
    lines.append(duration)

    density = report.headings_per_hour
    suffix = f" ({density}/h)" if density is not None else ""
    lines.append(f"headings {len(report.headings)}{suffix}")
    lines.extend(_heading_lines(report))

    lines.append(f"outline {report.outline_entries} entries")

    lines.append(f"themes {len(report.themes)} ({report.unthemed_concepts} concepts unthemed)")
    lines.extend(f"  {theme.concepts:>4}  {theme.name}" for theme in report.themes)

    lines.append(f"segments {len(report.segments)}")
    for segment in report.segments:
        state = "suppressed" if segment.suppressed else "kept"
        span = f"{format_time(segment.start)} - {format_time(segment.end)}"
        lines.append(
            f"  {span}  {segment.purpose}  {state}  {segment.units} unit"
            f"{'' if segment.units == 1 else 's'}"
        )

    lines.append(f"speakers {len(report.speakers)}")
    lines.extend(f"  {speaker.turns:>5} {speaker.label}" for speaker in report.speakers)

    captured = f" of {report.frames_captured} captured" if report.frames_captured else ""
    lines.append(f"frames {report.frames_kept} kept{captured}")

    lines.append(f"spellings {len(report.spellings)}")
    lines.extend(f"  {entry.count:>5} {entry.token}" for entry in report.spellings)

    return "\n".join(lines)


## Tests


def test_ordinary_words_do_not_crowd_out_the_names() -> None:
    """
    The measured case: one name spelled four ways, in prose full of capitalized sentence
    starts and back-channels. The variants have to surface and the filler must not.
    """
    text = (
        "Mhmm. Yeah. That is Omarchy. Then Omachi again. Well, Omarchy once more. "
        "Actually Amache. Because there is Omachi. Right. Something about Linux. "
        "It's Linux. I've used Linux."
    )

    found = {entry.token: entry.count for entry in spelling_variants([text])}

    assert found["Omarchy"] == 2
    assert found["Omachi"] == 2
    assert found["Amache"] == 1
    assert found["Linux"] == 3
    for filler in ("Mhmm", "Yeah", "That", "Then", "Well", "Actually", "Because", "Right"):
        assert filler not in found, f"{filler} is ordinary English, not a name"
    # Contractions are never a term to pass to --key-term.
    assert not [token for token in found if "'" in token or "’" in token]
    # Short capitalized tokens stay out too.
    assert "It" not in found


def test_the_spelling_list_is_capped_and_ranked() -> None:
    # Distinct alphabetic tokens only: a token built past "z" loses its tail to the
    # word pattern and collapses onto its neighbours, which is how the first version of
    # this check quietly generated 27 names instead of 50 and failed on the cap.
    names = [f"Xyzz{chr(ord('a') + i // 26)}{chr(ord('a') + i % 26)}" for i in range(50)]
    text = " ".join(f"{name} " * (60 - index) for index, name in enumerate(names))

    entries = spelling_variants([text])

    assert len(entries) == SPELLING_LIMIT
    assert [entry.count for entry in entries] == sorted(
        (entry.count for entry in entries), reverse=True
    )


def test_outline_entries_are_counted_inside_the_outline_block() -> None:
    body = (
        '<div class="transcript-outline" style="x">\n\n'
        "- **One**\n  - a point\n- **Two**\n  - another\n\n"
        '<div class="original">\n\n'
        "- **Not an outline entry**\n\n</div>\n"
    )

    assert _outline_entry_count(body) == 2
    assert _outline_entry_count("- **No outline block at all**") == 0


def test_heading_density_needs_a_duration() -> None:
    report = TranscriptReport(
        duration=7200.0,
        headings=[HeadingEntry("A", 1.0), HeadingEntry("B", 2.0)],
        outline_entries=0,
        themes=[],
        unthemed_concepts=0,
        segments=[],
        speakers=[],
        frames_kept=0,
        frames_captured=None,
        spellings=[],
    )

    assert report.headings_per_hour == 1.0
    assert "headings 2 (1.0/h)" in format_report_text(report)

    from dataclasses import replace

    unknown = replace(report, duration=None)
    assert unknown.headings_per_hour is None
    assert "headings 2\n" in format_report_text(unknown)
    assert "duration -" in format_report_text(unknown)


def test_a_long_heading_list_keeps_both_ends() -> None:
    report = TranscriptReport(
        duration=3600.0,
        headings=[HeadingEntry(f"Section {i}", float(i)) for i in range(206)],
        outline_entries=0,
        themes=[],
        unthemed_concepts=0,
        segments=[],
        speakers=[],
        frames_kept=0,
        frames_captured=None,
        spellings=[],
    )

    text = format_report_text(report)

    assert "Section 0" in text
    assert "Section 4" in text
    assert "Section 100" not in text
    assert "Section 201" in text
    assert "Section 205" in text
    assert f"… {206 - 2 * HEADING_LIST_EDGE} more" in text
    # The whole point of the cap: a five-hour recording still prints something readable.
    assert len(text.splitlines()) < 120
