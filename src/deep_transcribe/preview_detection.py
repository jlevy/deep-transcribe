"""
Finding the highlight reel at the front of a recording.

Many podcasts open with a teaser cut from the conversation that follows: a minute or two
of the best moments, spliced together out of order. It is worth marking, because those
moments then appear twice and the analysis counts them twice — on the measured example
the opening ran through AI progress, risk-taking, and the meaning of life inside two
minutes, all of which return properly later.

Detection is by near-duplicate text, not by inference. Speech-to-text does not produce
the same string twice for the same audio, so exact matching finds nothing; word shingles
survive the small substitutions ASR makes while still requiring the phrasing to really
match. A teaser is then the opening run of paragraphs whose words nearly all turn up
again later, and the boundary is where that stops being true.

This drafts a hint. It does not apply one — the file is the contract, and a person or an
agent decides what to do with what this proposes.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass

from deep_transcribe.transcript_index import RawUnit

log = logging.getLogger(__name__)

SHINGLE = 5
"""
Words per shingle.

Long enough that a match means the phrasing really matched — a 5-word run recurring by
chance in ordinary speech is rare — and short enough to survive the one-word
substitutions and dropped articles that speech-to-text produces on a second pass over
the same audio.
"""

ECHO_THRESHOLD = 0.5
"""Fraction of a paragraph's shingles that must reappear later for it to count as echoed."""

SEARCH_WINDOW_S = 900.0
"""
How far into the recording to look for a teaser.

A highlight reel is at the front by definition. Searching further finds recaps and
callbacks, which are part of the conversation and should not be cut.
"""

MIN_ECHOED_UNITS = 3
"""Below this, a couple of echoed paragraphs is likelier to be a coincidence than a reel."""

_WORD = re.compile(r"[a-z0-9']+")


def _shingles(text: str, size: int = SHINGLE) -> set[str]:
    words = _WORD.findall(text.lower())
    if len(words) < size:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i : i + size]) for i in range(len(words) - size + 1)}


@dataclass(frozen=True)
class PreviewClip:
    """A detected opening teaser."""

    start: float
    end: float
    units: int
    echoed_fraction: float
    """How much of the clip was found again later, as evidence for the reader of the hint."""


def detect_preview_clip(
    units: Sequence[RawUnit],
    window_s: float = SEARCH_WINDOW_S,
    threshold: float = ECHO_THRESHOLD,
) -> PreviewClip | None:
    """
    Find the opening run of paragraphs whose content recurs later in the recording.

    Returns None when the opening does not repeat, which is the common case: most
    recordings simply start.
    """
    if len(units) < MIN_ECHOED_UNITS * 2:
        return None
    start_time = units[0].start
    candidates = [u for u in units if u.start - start_time <= window_s]
    if len(candidates) < MIN_ECHOED_UNITS:
        return None

    # Everything after the search window is the body the opening might be quoting.
    body = units[len(candidates) :]
    if not body:
        return None
    later: set[str] = set()
    for unit in body:
        later |= _shingles(unit.text)
    if not later:
        return None

    echoed: list[bool] = []
    for unit in candidates:
        shingles = _shingles(unit.text)
        if not shingles:
            echoed.append(False)
            continue
        echoed.append(len(shingles & later) / len(shingles) >= threshold)

    # The clip is the opening run, tolerating a single un-echoed paragraph inside it: a
    # reel is spliced, so a stitch of host narration between clips is normal.
    end_index = 0
    misses = 0
    for index, hit in enumerate(echoed):
        if hit:
            end_index = index + 1
            misses = 0
        else:
            misses += 1
            if misses > 1:
                break
    if end_index < MIN_ECHOED_UNITS:
        return None

    clip = candidates[:end_index]
    fraction = sum(echoed[:end_index]) / end_index
    end_time = units[end_index].start if end_index < len(units) else clip[-1].start
    log.info(
        "Detected a preview clip: %d paragraphs to %.0fs, %.0f%% echoed later",
        end_index,
        end_time,
        fraction * 100,
    )
    return PreviewClip(
        start=clip[0].start,
        end=end_time,
        units=end_index,
        echoed_fraction=fraction,
    )


## Tests


def _unit(start: float, text: str) -> RawUnit:
    return RawUnit(key=f"{start:.2f}", start=start, label="A", text=text, section=0)


_LATER = [
    "There are decades where nothing happens and weeks where decades happen and we have"
    " seen decades of progress happen in the last nine months of artificial intelligence",
    "One of the things I always loved about race cars was when I would stumble out of the"
    " car after a long stint completely spent having given everything",
    "Creating life with another human that you love is literally the peak experience of"
    " being alive and nothing else comes close to it at all",
]


def test_detects_a_reel_whose_lines_return_later() -> None:
    units = [_unit(i * 40.0, text) for i, text in enumerate(_LATER)]
    units.append(_unit(200.0, "The following is a conversation with a guest on this show"))
    # The same three moments, an hour later, transcribed slightly differently — which is
    # what actually happens, since speech-to-text does not repeat itself exactly.
    units += [
        _unit(3600.0, _LATER[0].replace("nine months", "9 months")),
        _unit(4000.0, _LATER[1].replace("stumble out of the car", "stumble out the car")),
        _unit(5000.0, _LATER[2].replace("nothing else comes", "and nothing else comes")),
        _unit(6000.0, "Some entirely unrelated discussion of operating systems and tooling"),
    ]

    clip = detect_preview_clip(units)

    assert clip is not None
    assert clip.units == 3
    assert clip.start == 0.0
    assert clip.end == 200.0  # stops where the reel does, at the host's introduction
    assert clip.echoed_fraction == 1.0


def test_an_ordinary_opening_is_not_a_reel() -> None:
    units = [
        _unit(0.0, "Welcome to the show today we are going to talk about a few things"),
        _unit(40.0, "I am glad to be here and looking forward to the conversation ahead"),
        _unit(80.0, "Let us begin with the first topic which is how you got started"),
    ]
    units += [
        _unit(3600.0 + i * 100.0, f"Later discussion number {i} about something else")
        for i in range(6)
    ]

    assert detect_preview_clip(units) is None


def test_a_single_stitch_inside_the_reel_is_tolerated() -> None:
    # Reels are spliced, so a line of host narration between clips is normal.
    units = [
        _unit(0.0, _LATER[0]),
        _unit(40.0, "And much more in this episode brought to you by our partners"),
        _unit(80.0, _LATER[1]),
        _unit(120.0, "The following is a conversation with a guest on this show"),
    ]
    units += [_unit(3600.0, _LATER[0]), _unit(4000.0, _LATER[1])]
    units += [_unit(5000.0 + i * 100.0, f"Unrelated later talk {i}") for i in range(4)]

    clip = detect_preview_clip(units)

    assert clip is not None
    assert clip.units == 3  # through the second echoed line, not past the introduction


def test_too_short_a_recording_is_left_alone() -> None:
    assert detect_preview_clip([_unit(0.0, "Hello there")]) is None
    assert detect_preview_clip([]) is None
