"""
Segment hints: the file a person or an agent edits to say what part of a recording is
not the recording.

A long interview is not all interview. It opens with a highlight reel cut from the
conversation itself, breaks for read advertisements, and closes with an outro. Those
stretches are worth marking: they distort the concept map, they pad the outline, and a
reader scrolling the transcript wants them out of the way.

Detection can propose these, but the file is the contract. Everything downstream reads
the file, so a hint written by hand is worth exactly as much as one a model proposed —
which is what makes the loop work: run the tool, look at the output, edit the hints,
run again.

The format is deliberately small and forgiving. It is meant to be edited in a text
editor at a glance, so times may be written the way they are read.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

log = logging.getLogger(__name__)


class SegmentPurpose(StrEnum):
    """
    What a marked stretch is for.

    `promo` rather than `sponsor` because the read is not always for a sponsor — a host
    promoting their own book or course is the same thing structurally, and asking the
    writer of a hint to decide whose money it is helps nobody.
    """

    teaser = "teaser"
    """A highlight reel cut from the conversation, so its content appears twice."""

    intro = "intro"
    """Framing by the host: who the guest is, what the show is."""

    promo = "promo"
    """An advertisement or promotion, whoever it is for."""

    outro = "outro"
    """Sign-off, credits, calls to action."""

    other = "other"
    """Something to set aside that the vocabulary above does not name."""


VALID_PURPOSES = ", ".join(p.value for p in SegmentPurpose)
"""
The vocabulary, written out for the header of every hints file and for the error a
misspelled purpose raises. Built from the enum so neither can drift from it.
"""


SUPPRESSED_BY_DEFAULT = frozenset(
    {SegmentPurpose.teaser, SegmentPurpose.promo, SegmentPurpose.outro}
)
"""
Purposes that are excluded from analysis unless a hint says otherwise.

An intro is left in by default: it is short, it is genuinely about the conversation, and
the user asked to be able to pull out the introductory material rather than lose it.
"""

_HMS = re.compile(r"^(?:(?P<h>\d+):)?(?P<m>\d{1,2}):(?P<s>\d{1,2}(?:\.\d+)?)$")
_RANGE_SEP = re.compile(r"\s*(?:-|–|—|to)\s*")


def parse_time(text: str | float | int) -> float:
    """
    Read a time written as `H:MM:SS`, `MM:SS`, or plain seconds.

    Hints are written by hand against a transcript whose timestamps read `1:12:30`, so
    that is the form to accept first; seconds are allowed because that is what a program
    writes.
    """
    if isinstance(text, int | float):
        return float(text)
    raw = str(text).strip()
    match = _HMS.match(raw)
    if match:
        hours = float(match.group("h") or 0)
        return hours * 3600 + float(match.group("m")) * 60 + float(match.group("s"))
    try:
        return float(raw)
    except ValueError as error:
        raise ValueError(f"Cannot read a time from {text!r}; use H:MM:SS or seconds") from error


def format_time(seconds: float) -> str:
    """Write a time the way the transcript shows it, so a rewritten file still reads well."""
    total = int(round(seconds))
    return f"{total // 3600}:{total % 3600 // 60:02d}:{total % 60:02d}"


def format_span_outward(start: float, end: float) -> str:
    """
    Write a span that still covers everything it covered before it was rounded.

    `format_time` rounds to the nearest second in both directions, which is right for a
    label a person reads and wrong for a value a machine writes and then re-parses: a start
    of 4.56 becomes 0:00:05 and no longer contains the paragraph at 4.56, while an end of
    108.55 becomes 0:01:49 and reaches into the conversation. On the measured recording a
    suggested teaser lost its opening paragraph and gained two of the interview.

    So the start floors and the end ceils, and the span only ever grows by rounding.
    """
    lo = int(math.floor(start))
    hi = int(math.ceil(end))
    return f"{format_time(lo)} - {format_time(hi)}"


SPAN_TOLERANCE_S = 3.0
"""
How far two spans may differ and still mean the same stretch of recording.

Times survive a round trip through whole seconds, and a person marking a segment by eye
types the timestamp they can read, so comparing spans exactly compares the wrong thing.
"""


@dataclass(frozen=True)
class SegmentHint:
    """One marked stretch of the recording."""

    start: float
    end: float
    purpose: SegmentPurpose = SegmentPurpose.other
    suppress: bool | None = None
    """None means take the default for the purpose, so a file need not spell it out."""
    note: str = ""

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError(
                f"Segment ends before it starts: {format_time(self.start)}-{format_time(self.end)}"
            )

    @property
    def suppressed(self) -> bool:
        if self.suppress is not None:
            return self.suppress
        return self.purpose in SUPPRESSED_BY_DEFAULT

    def covers(self, t: float) -> bool:
        return self.start <= t < self.end


@dataclass
class SegmentHints:
    """Every hint for one recording, kept in the order they occur."""

    segments: list[SegmentHint] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.segments.sort(key=lambda s: s.start)

    def suppressed_at(self, t: float) -> SegmentHint | None:
        """The suppressing hint covering this moment, if any."""
        for segment in self.segments:
            if segment.suppressed and segment.covers(t):
                return segment
        return None

    def covering(
        self, start: float, end: float, tolerance: float = SPAN_TOLERANCE_S
    ) -> SegmentHint | None:
        """
        The hint that already accounts for this span, if there is one.

        Used to tell a fresh detection from one the user has already acted on. The
        tolerance is there because a written span is not the span it came from:
        `format_span_outward` rounds to whole seconds, and a hand-edited file rounds to
        whatever the person reading the transcript typed. A hint a few seconds shy of the
        detected span still means the same stretch of tape.

        Suppression is not consulted: a hint written over a stretch is a decision about
        it either way, and re-proposing what someone deliberately left in would be the
        same nuisance.
        """
        for segment in self.segments:
            if segment.start <= start + tolerance and segment.end + tolerance >= end:
                return segment
        return None

    def overlaps(self) -> list[tuple[SegmentHint, SegmentHint]]:
        """
        Pairs that overlap.

        Not an error — a promo inside an intro is a real thing — but the caller may want
        to say so, since an accidental overlap usually means a typo in a time.
        """
        pairs: list[tuple[SegmentHint, SegmentHint]] = []
        for first, second in zip(self.segments, self.segments[1:], strict=False):
            if second.start < first.end:
                pairs.append((first, second))
        return pairs


def parse_hints(data: object) -> SegmentHints:
    """
    Read hints from already-loaded YAML or JSON.

    A malformed entry is dropped with a warning rather than failing the run: the file is
    edited by hand between runs, and losing a five-hour analysis to one mistyped time
    would make people stop editing it.

    An unrecognised `purpose` is the exception and stops the run — see `_read_purpose`.
    """
    if data is None:
        return SegmentHints()
    if not isinstance(data, dict):
        raise ValueError("Segment hints must be a mapping with a `segments` list")
    raw_list = cast(dict[str, Any], data).get("segments")
    if raw_list is None:
        return SegmentHints()
    if not isinstance(raw_list, list):
        raise ValueError("`segments` must be a list")

    hints: list[SegmentHint] = []
    for index, raw in enumerate(cast(list[object], raw_list)):
        if not isinstance(raw, dict):
            log.warning("Skipping segment %d: not a mapping", index + 1)
            continue
        entry = cast(dict[str, Any], raw)
        # Read outside the forgiving block below, so the error reaches the caller instead
        # of being logged and the entry quietly dropped.
        purpose = _read_purpose(entry, index)
        try:
            start, end = _read_span(entry)
            suppress = entry.get("suppress")
            hints.append(
                SegmentHint(
                    start=start,
                    end=end,
                    purpose=purpose,
                    suppress=bool(suppress) if suppress is not None else None,
                    note=str(entry.get("note") or ""),
                )
            )
        except ValueError as error:
            log.warning("Skipping segment %d: %s", index + 1, error)
    return SegmentHints(hints)


def _read_purpose(entry: dict[str, Any], index: int) -> SegmentPurpose:
    """
    Read `purpose`, refusing any word the vocabulary does not have.

    An unknown purpose used to become `other`, which is the one kind of mistake in this
    file that cannot be seen: each purpose carries a default `suppress` and a label, so
    `purpose: cold_open` silently changed both what was excluded from the analysis and
    what the collapsed block was called — and the file the tool wrote back said
    `purpose: other`, with nothing to explain where the word went.

    So this is fatal where a mistyped time is not. A bad time drops one entry and says
    so; a bad purpose would keep the entry and change what it means.
    """
    raw = entry.get("purpose")
    if raw is None or not str(raw).strip():
        return SegmentPurpose.other
    text = str(raw).strip().lower()
    try:
        return SegmentPurpose(text)
    except ValueError as error:
        raise ValueError(
            f'Unknown segment purpose "{text}" for {_describe_entry(entry, index)}; '
            f"valid purposes are: {VALID_PURPOSES}"
        ) from error


def _describe_entry(entry: dict[str, Any], index: int) -> str:
    """Point at an entry the way its writer wrote it, so they can find the line."""
    at = entry.get("at")
    if at is not None:
        return f'"{str(at).strip()}"'
    start, end = entry.get("start"), entry.get("end")
    if start is not None and end is not None:
        return f'"{start} - {end}"'
    return f"segment {index + 1}"


def _read_span(entry: dict[str, Any]) -> tuple[float, float]:
    """Accept either `at: "0:00 - 3:14"` or separate `start` and `end`."""
    at = entry.get("at")
    if at is not None:
        parts = _RANGE_SEP.split(str(at).strip())
        if len(parts) != 2:
            raise ValueError(f"Cannot read a range from {at!r}; use `START - END`")
        return parse_time(parts[0]), parse_time(parts[1])
    if "start" in entry and "end" in entry:
        return parse_time(entry["start"]), parse_time(entry["end"])
    raise ValueError("Needs either `at: START - END` or both `start` and `end`")


def load_hints(path: Path) -> SegmentHints:
    """Read a hints file, treating a missing file as no hints."""
    if not path.exists():
        return SegmentHints()
    import yaml

    return parse_hints(yaml.safe_load(path.read_text()))


HINTS_HEADER = f"""\
# Segment hints — edit and rerun.
#
# Each entry marks a stretch of the recording that is not the recording: a teaser cut
# from the conversation, an ad read, an outro. Suppressed segments are left out of the
# analysis and collapsed in the transcript rather than deleted.
#
# Times read as H:MM:SS. Purpose is one of: {VALID_PURPOSES}.
# Any other word is an error rather than a guess, because the purpose decides both what
# is left out of the analysis and what the collapsed block is called.
# `suppress` is optional; teaser, promo and outro are suppressed by default, intro is not.
#
# Rerunning after an edit reuses the transcript and everything up to the section
# headings, and redoes only the analysis and the page.
"""


def write_hints(path: Path, hints: SegmentHints, title: str | None = None) -> None:
    """
    Write hints back out, in the readable form, comments and all.

    Written by hand rather than by a YAML dumper because the header explains the file to
    whoever opens it next, and a dumper would drop it on the next rewrite.
    """
    lines = [HINTS_HEADER]
    if title:
        lines.append(f"# Recording: {title}\n")
    lines.append("\nsegments:\n")
    if not hints.segments:
        lines.append("  # No segments marked yet.\n  []\n")
    for segment in hints.segments:
        lines.append(f'  - at: "{format_span_outward(segment.start, segment.end)}"\n')
        lines.append(f"    purpose: {segment.purpose.value}\n")
        if segment.suppress is not None:
            lines.append(f"    suppress: {str(segment.suppress).lower()}\n")
        if segment.note:
            escaped = segment.note.replace('"', "'")
            lines.append(f'    note: "{escaped}"\n')
    path.write_text("".join(lines))


## Tests


def test_times_read_the_way_a_transcript_writes_them() -> None:
    assert parse_time("1:12:30") == 4350.0
    assert parse_time("3:14") == 194.0
    assert parse_time("0:03:14.5") == 194.5
    assert parse_time(90.5) == 90.5
    assert parse_time("90.5") == 90.5
    assert format_time(4350) == "1:12:30"
    assert format_time(194) == "0:03:14"

    import pytest

    with pytest.raises(ValueError, match="Cannot read a time"):
        parse_time("half past")


def test_a_hint_takes_the_default_for_its_purpose() -> None:
    assert SegmentHint(0, 10, SegmentPurpose.promo).suppressed
    assert SegmentHint(0, 10, SegmentPurpose.teaser).suppressed
    assert SegmentHint(0, 10, SegmentPurpose.outro).suppressed
    # An intro is short and genuinely about the conversation, so it stays in.
    assert not SegmentHint(0, 10, SegmentPurpose.intro).suppressed
    # An explicit value always wins over the default, both ways.
    assert not SegmentHint(0, 10, SegmentPurpose.promo, suppress=False).suppressed
    assert SegmentHint(0, 10, SegmentPurpose.intro, suppress=True).suppressed


def test_parses_both_span_forms_and_sorts() -> None:
    hints = parse_hints(
        {
            "segments": [
                {"at": "1:00:00 - 1:02:30", "purpose": "promo"},
                {"start": "0:00", "end": "3:14", "purpose": "teaser", "note": "highlights"},
            ]
        }
    )

    assert [h.start for h in hints.segments] == [0.0, 3600.0]
    assert hints.segments[0].purpose is SegmentPurpose.teaser
    assert hints.segments[0].note == "highlights"
    assert hints.segments[1].end == 3750.0


def test_a_bad_entry_is_dropped_not_fatal() -> None:
    # The file is edited by hand between runs; one mistyped time must not cost the run.
    hints = parse_hints(
        {
            "segments": [
                {"at": "0:00 - 3:14", "purpose": "teaser"},
                {"at": "not a range", "purpose": "promo"},
                {"at": "5:00 - 4:00", "purpose": "promo"},
                {"purpose": "promo"},
                "not even a mapping",
                {"at": "9:00 - 9:30", "note": "no purpose named"},
            ]
        }
    )

    assert len(hints.segments) == 2
    # A missing purpose is the one that still falls back to `other`. An unrecognised one
    # does not — see below.
    assert hints.segments[1].purpose is SegmentPurpose.other


def test_an_unknown_purpose_says_so_instead_of_becoming_other() -> None:
    """
    The measured case: a hand-written `purpose: cold_open` was accepted, silently read as
    `other`, and written back out as `purpose: other`. Because a purpose decides both
    default suppression and the collapse label, that changed the run with no signal. The
    error has to name the word, the entry it was in, and what would have worked.
    """
    import pytest

    with pytest.raises(ValueError) as caught:
        parse_hints({"segments": [{"at": "0:00 - 0:20", "purpose": "cold_open"}]})

    message = str(caught.value)
    assert "cold_open" in message, "the error must name the word the writer typed"
    assert "0:00 - 0:20" in message, "the error must point at the entry it came from"
    for purpose in SegmentPurpose:
        assert purpose.value in message, f"the error must offer {purpose.value}"

    # And an entry with no readable times still gets pointed at somehow.
    with pytest.raises(ValueError, match="segment 1"):
        parse_hints({"segments": [{"purpose": "cold_open"}]})


def test_every_valid_purpose_still_parses() -> None:
    # The list in the error is only useful if everything on it works.
    for purpose in SegmentPurpose:
        hints = parse_hints({"segments": [{"at": "0:00 - 0:20", "purpose": purpose.value}]})
        assert hints.segments[0].purpose is purpose

    # Matching stays case- and whitespace-tolerant: hints are typed by hand.
    assert (
        parse_hints({"segments": [{"at": "0:00 - 0:20", "purpose": "  PROMO "}]})
        .segments[0]
        .purpose
        is SegmentPurpose.promo
    )


def test_an_unknown_purpose_in_a_real_file_stops_the_load(tmp_path: Path) -> None:
    """
    Through `load_hints`, which is what the CLI calls for `--segments`. The check lives
    beside a block that logs and drops bad entries, so a version of this that only ever
    ran against `parse_hints` in memory could pass while the file path swallowed it.
    """
    import pytest

    path = tmp_path / "segments.yml"
    path.write_text('segments:\n  - at: "0:00 - 0:20"\n    purpose: cold_open\n')

    with pytest.raises(ValueError, match="cold_open"):
        load_hints(path)


def test_suppressed_at_finds_the_covering_segment() -> None:
    hints = parse_hints(
        {
            "segments": [
                {"at": "0:00 - 3:14", "purpose": "teaser"},
                {"at": "10:00 - 12:00", "purpose": "intro"},
            ]
        }
    )

    assert hints.suppressed_at(60.0) is not None
    assert hints.suppressed_at(200.0) is None  # past the teaser
    assert hints.suppressed_at(650.0) is None  # inside the intro, which is not suppressed


def test_covering_recognizes_a_span_already_marked() -> None:
    """
    A detected clip is compared against hints that were written and reparsed, so the
    times no longer match to the decimal. What matters is whether someone has already
    said something about that stretch.
    """
    hints = parse_hints(
        {
            "segments": [
                # What the tool writes for a clip detected at 4.56 - 108.55.
                {"at": "0:00:04 - 0:01:49", "purpose": "teaser"},
                {"at": "1:00:00 - 1:02:30", "purpose": "promo", "suppress": False},
            ]
        }
    )

    assert hints.covering(4.56, 108.55) is not None
    # Hand-typed round numbers a couple of seconds inside the clip still mean the clip.
    assert parse_hints({"segments": [{"at": "0:00:06 - 0:01:47"}]}).covering(4.56, 108.55)
    # A hint that only caught the opening paragraph has not accounted for the rest.
    assert hints.covering(4.56, 600.0) is None
    assert parse_hints({"segments": [{"at": "0:00:04 - 0:00:30"}]}).covering(4.56, 108.55) is None
    # A stretch the user deliberately kept is still a stretch they decided about.
    assert hints.covering(3605.0, 3740.0) is not None
    assert SegmentHints().covering(4.56, 108.55) is None


def test_overlaps_are_reported_not_rejected() -> None:
    hints = parse_hints(
        {
            "segments": [
                {"at": "0:00 - 10:00", "purpose": "intro"},
                {"at": "5:00 - 6:00", "purpose": "promo"},
            ]
        }
    )

    assert len(hints.overlaps()) == 1
    assert len(hints.segments) == 2  # a promo inside an intro is legitimate


def test_roundtrips_through_a_file(tmp_path: Path) -> None:
    original = parse_hints(
        {
            "segments": [
                {"at": "0:00 - 3:14", "purpose": "teaser", "note": 'the "highlight" reel'},
                {"at": "1:00:00 - 1:02:30", "purpose": "promo", "suppress": False},
            ]
        }
    )
    path = tmp_path / "segments.yml"

    write_hints(path, original, title="A recording")
    reloaded = load_hints(path)

    assert [(h.start, h.end, h.purpose) for h in reloaded.segments] == [
        (h.start, h.end, h.purpose) for h in original.segments
    ]
    assert reloaded.segments[1].suppress is False
    assert not reloaded.segments[1].suppressed
    # The header survives, because it is what explains the file to the next reader.
    assert "edit and rerun" in path.read_text()


def test_a_missing_or_empty_file_is_no_hints(tmp_path: Path) -> None:
    assert load_hints(tmp_path / "nothing.yml").segments == []
    empty = tmp_path / "empty.yml"
    empty.write_text("segments:\n")
    assert load_hints(empty).segments == []
    assert parse_hints(None).segments == []


def test_a_hint_edit_is_the_only_thing_that_changes_between_runs() -> None:
    """
    Two hint files describing the same segments must produce the same hints, whatever
    order their keys are written in. The pipeline hashes the file's YAML text, so a
    reordered but equivalent file that parsed differently would silently invalidate the
    analysis cache for no reason.
    """
    one = parse_hints({"segments": [{"at": "0:00 - 3:14", "purpose": "teaser", "note": "reel"}]})
    other = parse_hints(
        {"segments": [{"note": "reel", "purpose": "teaser", "start": "0:00", "end": "3:14"}]}
    )

    assert [(h.start, h.end, h.purpose, h.note, h.suppressed) for h in one.segments] == [
        (h.start, h.end, h.purpose, h.note, h.suppressed) for h in other.segments
    ]


def test_a_written_span_still_covers_the_paragraphs_it_described() -> None:
    """
    The measured case from the real Lex transcript: the detector found a teaser at
    start=4.56, end=108.55, and the file written for it said "0:00:05 - 0:01:49" — which no
    longer contained the paragraph at 4.56 and did contain two paragraphs of the interview.
    A machine-written span must only ever grow when rounded.
    """
    hints = SegmentHints(
        [SegmentHint(start=4.56, end=108.55, purpose=SegmentPurpose.teaser, note="")]
    )
    written = format_span_outward(hints.segments[0].start, hints.segments[0].end)
    assert written == "0:00:04 - 0:01:49"

    reparsed = parse_hints({"segments": [{"at": written, "purpose": "teaser"}]})
    lo, hi = reparsed.segments[0].start, reparsed.segments[0].end
    assert lo <= 4.56, "the written span lost its first paragraph"
    assert hi >= 108.55, "the written span lost its last paragraph"


def test_writing_and_reparsing_a_hint_file_keeps_every_unit(tmp_path: Path) -> None:
    """Round-trip through the file the tool actually writes."""
    units = [4.56, 31.46, 44.12, 61.03, 69.12, 108.55]
    hints = SegmentHints(
        [SegmentHint(start=units[0], end=units[-1], purpose=SegmentPurpose.teaser, note="")]
    )
    path = tmp_path / "segments.yml"
    write_hints(path, hints)

    reloaded = load_hints(path)
    span = reloaded.segments[0]
    covered = [t for t in units if span.start <= t <= span.end]
    assert covered == units, f"round trip dropped {set(units) - set(covered)}"
