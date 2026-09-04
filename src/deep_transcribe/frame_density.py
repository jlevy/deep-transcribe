"""
Thinning frame captures so a long recording does not bury the page in thumbnails.

`insert_frame_captures` emits one frame per timestamped paragraph and filters consecutive
near-duplicates. That is the right shape for a short video and does not scale: measured
on a 5.3-hour interview it produced 502 frames — 95 an hour, 115 MB of jpgs, a continuous
ribbon down the gutter of a 188,000 px page. The similarity filter had already removed
64% and still left that.

The cap is expressed as a density rather than a fixed number, so a recording is judged by
how crowded its gutter is rather than by a count that means different things at different
lengths.

The density alone is not enough, because short media is legitimately dense: the project's
own showcase, SNL "Hotel Check In", is 4:26 with 15 frames — 231 an hour, five times any
sane long-form target — and it reads perfectly well, because 15 thumbnails is simply not
many. Judging it by density gutted it to 3. So a floor on the absolute count runs
alongside the density, and a document with few frames is left alone whatever its density.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)

TARGET_FRAMES_PER_HOUR = 45.0
"""
Frames per hour to thin a long recording down to.

Measured: the 5.3-hour interview produced 502 frames at 95 an hour, a continuous ribbon
down a 188,000 px page. At 45 an hour the same recording lands near 240, which reads as a
column of stills rather than a ribbon.

This is a long-form figure and is not derived from the short example — an earlier version
of this docstring claimed a "22-minute example at 41 an hour", which does not exist in
this repository. That number came from a synthetic test fixture, and calibrating to it is
what caused the showcase example to lose 12 of its 15 frames.
"""

MIN_FRAMES_KEPT = 20
"""
Never thin a document that has fewer frames than this, and never thin one below it.

The density target is meaningless for a short recording: SNL "Hotel Check In" is 4:26 with
15 frames, and 45 an hour would allow it 3. Twenty is above every short example in the
repository and far below the point where a page starts to feel like a ribbon, so it keeps
the stated invariant — short media is untouched — true rather than aspirational.
"""

_FRAME_IMG = re.compile(
    r'\n*<img class="frame-capture" src="(?P<src>[^"]+)" alt="Frame at '
    r'(?P<ts>\d+(?:\.\d+)?) seconds"[^>]*>\n*'
)


def thin_frame_captures(
    body: str,
    assets_dir: Path | None = None,
    target_per_hour: float = TARGET_FRAMES_PER_HOUR,
) -> tuple[str, int]:
    """
    Drop frames that sit too close to the one before them, and delete their files.

    Keeps the frame nearest each of a target number of evenly spaced moments, so what
    survives is spread across the recording rather than clustered wherever the speaker
    paused often. Returns the new body and how many frames were removed.
    """
    matches = list(_FRAME_IMG.finditer(body))
    if len(matches) < 2:
        return body, 0

    times = [float(m.group("ts")) for m in matches]
    span = times[-1] - times[0]
    if span <= 0:
        return body, 0
    # A short document is left alone whatever its density; see MIN_FRAMES_KEPT.
    if len(matches) <= MIN_FRAMES_KEPT:
        return body, 0
    target = max(MIN_FRAMES_KEPT, round(target_per_hour * span / 3600))
    if target < 1 or len(matches) <= target:
        return body, 0

    # Pick the frame nearest each of `target` evenly spaced moments, rather than walking
    # forward with a minimum gap. A greedy gap undershoots whenever the source spacing
    # does not divide into it — on the measured 502-frame document it kept 168 of a
    # target of 237, because every second frame fell just inside the gap and was skipped.
    # Where the recording has a long stretch with no frames, two consecutive ideal
    # moments can land nearest the same frame. Without a floor the second pick slides to
    # the neighbour, which on the real document produced kept pairs half a second apart.
    floor_gap = span / target / 2
    keep: list[int] = []
    index = 0
    for step in range(target):
        ideal = times[0] + span * step / max(1, target - 1)
        while index + 1 < len(times) and abs(times[index + 1] - ideal) <= abs(times[index] - ideal):
            index += 1
        if not keep or (index > keep[-1] and times[index] - times[keep[-1]] >= floor_gap):
            keep.append(index)
    kept = set(keep)

    pieces: list[str] = []
    cursor = 0
    removed_srcs: list[str] = []
    for index, match in enumerate(matches):
        if index in kept:
            continue
        pieces.append(body[cursor : match.start()])
        # Leave one newline behind so surrounding paragraphs stay separated.
        pieces.append("\n\n")
        cursor = match.end()
        removed_srcs.append(match.group("src"))
    pieces.append(body[cursor:])

    if assets_dir is not None:
        for src in removed_srcs:
            path = assets_dir.parent / src
            try:
                path.unlink()
            except OSError:
                # A frame already gone is not a reason to fail the export.
                log.debug("Could not delete thinned frame: %s", path)

    log.info(
        "Thinned frame captures from %d to %d (%.0f per hour over %.1f h)",
        len(matches),
        len(kept),
        len(kept) / (span / 3600),
        span / 3600,
    )
    return "".join(pieces), len(matches) - len(kept)


## Tests


def _doc(times: list[float]) -> str:
    return "".join(
        f"Paragraph {i}.\n"
        f'<img class="frame-capture" src="a.assets/f{i}.jpg" alt="Frame at {t} seconds" />\n\n'
        for i, t in enumerate(times)
    )


def test_short_media_is_untouched() -> None:
    # 15 frames over 22 minutes is 41 an hour, under the target.
    body = _doc([i * 88.0 for i in range(15)])

    thinned, removed = thin_frame_captures(body)

    assert removed == 0
    assert thinned == body


def test_dense_long_media_is_thinned_to_the_target() -> None:
    # 502 frames evenly over 5.26 hours, the measured shape.
    times = [i * 37.7 for i in range(502)]
    body = _doc(times)

    thinned, removed = thin_frame_captures(body)

    kept = thinned.count('class="frame-capture"')
    assert removed == 502 - kept
    assert 220 <= kept <= 250, kept
    # Every surviving frame keeps its paragraph, and the text is never touched.
    assert thinned.count("Paragraph ") == 502


def test_thinning_spreads_frames_rather_than_taking_a_prefix() -> None:
    times = [i * 10.0 for i in range(400)]  # 400 frames over 66 minutes

    thinned, _ = thin_frame_captures(_doc(times))

    kept = [float(m.group("ts")) for m in _FRAME_IMG.finditer(thinned)]
    assert kept[0] == 0.0
    # The last kept frame is near the end, not a quarter of the way in.
    assert kept[-1] > times[-1] * 0.9


def test_kept_frames_are_never_bunched_together() -> None:
    # A long stretch with no frames, then a dense cluster: the shape that produced kept
    # pairs half a second apart before the floor.
    times = [i * 5.0 for i in range(200)] + [3600.0 + i * 5.0 for i in range(200)]

    thinned, _ = thin_frame_captures(_doc(times))

    kept = [float(m.group("ts")) for m in _FRAME_IMG.finditer(thinned)]
    assert len(kept) == len(set(kept))
    gaps = [b - a for a, b in zip(kept, kept[1:], strict=False)]
    assert min(gaps) >= 20.0, min(gaps)


def test_a_single_frame_is_left_alone() -> None:
    body = _doc([1.0])

    assert thin_frame_captures(body) == (body, 0)


def test_thinning_an_already_thinned_document_changes_nothing() -> None:
    """
    Thinning runs after every frame-capture step, including reruns that hit the cache and
    return a body already thinned. A second pass must be a no-op, or each rerun would
    quietly strip more frames until none were left.
    """
    body = _doc([i * 37.7 for i in range(502)])

    once, first_removed = thin_frame_captures(body)
    twice, second_removed = thin_frame_captures(once)

    assert first_removed > 0
    assert second_removed == 0
    assert twice == once


def test_the_real_showcase_example_is_untouched() -> None:
    """
    The actual shape of the project's showcase, SNL "Hotel Check In": 15 frames over 4:26.

    The previous target was calibrated against a "22-minute example at 41 frames an hour"
    that does not exist in this repository — it was back-derived from the synthetic fixture
    in `test_short_media_is_untouched`, which spaces 15 frames 88 s apart and so happens to
    sit under the cap. Measured against the real example the same code removed 12 of 15
    frames, contradicting the documented invariant.
    """
    times = [
        1.84,
        18.0,
        34.5,
        52.0,
        69.0,
        86.5,
        104.0,
        114.3,
        131.0,
        148.5,
        166.0,
        183.5,
        201.0,
        218.5,
        236.0,
    ]
    assert len(times) == 15
    span_hours = (times[-1] - times[0]) / 3600
    assert round(len(times) / span_hours) == 231  # five times the long-form target

    body, removed = thin_frame_captures(_doc(times))

    assert removed == 0, "the showcase example lost frames"
    assert body.count('class="frame-capture"') == 15


def test_a_long_recording_is_still_thinned_hard() -> None:
    """The floor must not blunt the case the cap exists for: 502 frames over 5.3 hours."""
    span = 5.3 * 3600
    times = [i * span / 501 for i in range(502)]

    _body, removed = thin_frame_captures(_doc(times))

    kept = 502 - removed
    assert 200 <= kept <= 260, f"expected roughly 240 kept, got {kept}"


def test_the_floor_is_never_crossed() -> None:
    """A recording just above the floor is thinned to the floor, not below it."""
    # 30 frames over 20 minutes: 90 an hour, above the target, but only 30 frames.
    times = [i * 1200 / 29 for i in range(30)]

    _body, removed = thin_frame_captures(_doc(times))

    assert 30 - removed >= MIN_FRAMES_KEPT
