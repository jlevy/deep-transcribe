"""
Thinning frame captures so a long recording does not bury the page in thumbnails.

`insert_frame_captures` emits one frame per timestamped paragraph and filters consecutive
near-duplicates. That is the right shape for a short video and does not scale: measured
on a 5.3-hour interview it produced 502 frames — 95 an hour, 115 MB of jpgs, a continuous
ribbon down the gutter of a 188,000 px page. The similarity filter had already removed
64% and still left that.

The cap is expressed as a density rather than a fixed number, and it is set to the
density that already works: the 22-minute example runs at about 41 frames an hour and
reads well. Anything at or below the target is left exactly as it is, so short media
never changes.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)

TARGET_FRAMES_PER_HOUR = 45.0
"""
Frames per hour to thin down to, matched to what short media already does.

The SNL example sits at 41 an hour and looks right, so a recording under this density is
untouched and one above it is thinned to roughly this. Five hours lands near 240 rather
than 502.
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
    target = round(target_per_hour * span / 3600)
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
