"""
Cutting a long transcript into pieces small enough for one model call.

Three stages used to send the whole document: the concept map, the outline, and the
synopsis. That has a ceiling — twelve hours is about 170k tokens and fourteen does not
fit at all — but the ceiling is the lesser problem. The real one arrives long before it:
a budget written for one call does not grow with the material, so a five-hour recording
gets a thinner analysis per hour than a five-minute one.

Chunks are time-based and cut at section seams. Time sets the budget, so the number of
calls is proportional to length rather than to the number of sections. Sections set the
actual cut, because the sectioning pass has already found where topics change and those
boundaries are the natural seams.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from deep_transcribe.segment_hints import SegmentHints
from deep_transcribe.transcript_index import RawUnit, scan_raw_units, scan_section_offsets

log = logging.getLogger(__name__)

CHUNK_TARGET_SECONDS = 1800.0
"""
Target audio duration per call, before snapping to section boundaries.

Half an hour gives about 11 calls on a five-hour recording and 24 on twelve hours, with
chunks even enough that a per-chunk budget means the same thing throughout. An hour was
measured too and leaves a ragged short tail.
"""


def drop_suppressed(units: Sequence[RawUnit], hints: SegmentHints | None) -> list[RawUnit]:
    """
    Remove units inside a suppressed segment, so the analysis never sees them.

    This is where a hint earns its keep. A teaser is the same words as the conversation
    it advertises, so leaving it in doubles the weight of whatever it previews; an ad
    read is not about the conversation at all. Both distort a concept map and pad an
    outline. The transcript itself keeps every word — suppression is about what the
    analysis reads, not about what the reader can see.
    """
    if hints is None or not hints.segments:
        return list(units)
    kept = [unit for unit in units if hints.suppressed_at(unit.start) is None]
    if len(kept) != len(units):
        log.info(
            "Excluded %d of %d units inside suppressed segments", len(units) - len(kept), len(units)
        )
    return kept


def plan_chunks(
    units: Sequence[RawUnit], target_seconds: float = CHUNK_TARGET_SECONDS
) -> list[list[RawUnit]]:
    """
    Group units into chunks of about `target_seconds`, cut at section seams.

    A chunk closes once it has covered the target duration and the next unit starts a new
    section. A section longer than the target becomes a chunk on its own rather than
    being split, since splitting a topic is what this exists to avoid. Anything shorter
    than the target is a single chunk, which is the previous whole-document behavior.
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


def split_body(
    body: str,
    target_seconds: float = CHUNK_TARGET_SECONDS,
    hints: SegmentHints | None = None,
) -> list[str]:
    """
    Cut the document body itself into chunks, on the same seams `plan_chunks` finds.

    The concept map reads units; the outline and synopsis read prose, headings included,
    so they need the text rather than the scan. Both cut in the same places, so the two
    analyses describe the same stretches of the recording.

    Sections whose every unit is suppressed do not appear in any chunk. A section is the
    smallest piece this can drop, because a chunk is built from whole sections — a promo
    that sits inside a section leaves that section in place, and trimming to the exact
    span is a separate job with its own boundary-snapping rules.
    """
    units = scan_raw_units(body)
    surviving = drop_suppressed(units, hints)
    if not surviving:
        return [body] if body else []

    offsets = scan_section_offsets(body)
    if not offsets:
        # Nothing to cut on. Chunking needs headings, so the body stays whole.
        return [body]

    def section_text(index: int) -> str:
        begin = offsets[index]
        finish = offsets[index + 1] if index + 1 < len(offsets) else len(body)
        return body[begin:finish].strip()

    chunks = plan_chunks(surviving, target_seconds)
    pieces: list[str] = []
    for chunk in chunks:
        sections = sorted({unit.section for unit in chunk if 0 <= unit.section < len(offsets)})
        text = "\n\n".join(filter(None, (section_text(i) for i in sections)))
        if text:
            pieces.append(text)
    return pieces or [body]


## Tests


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


def test_split_body_cuts_at_headings() -> None:
    def section(index: int, minutes: int) -> str:
        return (
            f"## Section {index}\n\n**Alice:** Text {index}.\n"
            '<span class="citation timestamp-link" data-src="r.yml" '
            f'data-timestamp="{minutes * 60}.00"><a href="https://x">t</a></span>\n\n'
        )

    body = "".join(section(i, i * 10) for i in range(9))  # 0, 10, ... 80 minutes

    pieces = split_body(body, target_seconds=1800.0)

    assert len(pieces) == 3
    assert all(piece.startswith("## Section") for piece in pieces)
    # Each chunk covers exactly 30 min: sections 0-2, 3-5, 6-8.
    assert [p.split("\n", 1)[0] for p in pieces] == ["## Section 0", "## Section 3", "## Section 6"]
    # Nothing is lost or duplicated.
    assert sum(p.count("**Alice:**") for p in pieces) == 9


def test_split_body_keeps_short_media_whole() -> None:
    body = (
        "## Only\n\n**Alice:** Hi.\n"
        '<span class="citation timestamp-link" data-src="r.yml" data-timestamp="1.00">'
        '<a href="https://x">t</a></span>\n'
    )

    # One chunk holding the whole document, trimmed at the edges.
    assert split_body(body) == [body.strip()]
    assert split_body("") == []


def test_suppressed_units_are_dropped_before_chunking() -> None:
    from deep_transcribe.segment_hints import parse_hints

    units = [_unit(i * 60.0, i // 4) for i in range(40)]  # 40 minutes
    hints = parse_hints(
        {
            "segments": [
                {"at": "0:00 - 5:00", "purpose": "teaser"},
                {"at": "20:00 - 22:00", "purpose": "intro"},  # not suppressed by default
            ]
        }
    )

    kept = drop_suppressed(units, hints)

    assert [u.start for u in kept][0] == 300.0  # the teaser is gone
    assert 1200.0 in [u.start for u in kept]  # the intro stays
    assert drop_suppressed(units, None) == units


def test_split_body_leaves_out_suppressed_stretches() -> None:
    from deep_transcribe.segment_hints import parse_hints

    def section(index: int, minutes: int) -> str:
        return (
            f"## Section {index}\n\n**Alice:** Text {index}.\n"
            '<span class="citation timestamp-link" data-src="r.yml" '
            f'data-timestamp="{minutes * 60}.00"><a href="https://x">t</a></span>\n\n'
        )

    body = "".join(section(i, i * 10) for i in range(9))  # 0 to 80 minutes
    hints = parse_hints({"segments": [{"at": "0:00 - 15:00", "purpose": "promo"}]})

    pieces = split_body(body, target_seconds=1800.0, hints=hints)

    # The first two sections fall inside the promo, so the chunking starts after it.
    assert pieces[0].startswith("## Section 2")
