"""
Publisher chapters as the transcript's section skeleton.

A windowed heading stage judges a topic change from the 128 paragraphs in front of it, so
on a five-hour recording it inserts one heading every minute or two: Lex Fridman #501 came
back with 206 of them, and because the outline, timeline and analytics views are all built
from the same `##` skeleton, every one of those surfaces inherited 206 sections.

The publisher already wrote the answer down. YouTube publishes 23 chapters for that video
with boundaries a human chose, and `transcript_index` reads only `##` headings — `###` is
invisible to the index, to the outline and synopsis chunking, and to the timeline. So the
chapters become the `##` skeleton and the model's headings are demoted a level: every
downstream surface gets the 23 human sections, the model's 206 survive as sub-headings
inside them, and no code below this point has to change.
"""

from __future__ import annotations

import bisect
import logging
import re
from dataclasses import dataclass
from typing import Any, cast

from kash.exec import kash_action
from kash.exec.preconditions import has_simple_text_body
from kash.model import Item
from kash.utils.errors import InvalidInput

log = logging.getLogger(__name__)

CHAPTERS_KEY = "chapters"
"""Where the publisher's chapter list lives in a resource's `extra`."""

# The citation spans `backfill_timestamps` writes and `normalize_timestamp_citations`
# tidies. `data-timestamp` is the START of the paragraph whose text the span closes, which
# is what makes a citation the anchor a chapter boundary can be resolved against.
_CITATION_PATTERN = re.compile(
    r'<span class="citation timestamp-link"[^>]*\bdata-timestamp="(?P<ts>\d+(?:\.\d+)?)"'
)

# Deliberately the same shape as `transcript_index._H2_PATTERN`, restricted to a single
# line: what that pattern sees is the section skeleton, so what this module writes and
# rewrites has to be exactly the same set of lines.
_H2_LINE_PATTERN = re.compile(r"^##(?!#)[ \t]+(?P<heading>.+?)[ \t]*$", re.MULTILINE)

# A block that is nothing but a heading, at any level.
_HEADING_BLOCK_PATTERN = re.compile(r"^#{1,6}[ \t]+\S[^\n]*$")

# One or more blank lines: the Markdown block separator.
_BLOCK_BREAK_PATTERN = re.compile(r"\n(?:[ \t]*\n)+")


@dataclass(frozen=True)
class Chapter:
    """One publisher chapter, in seconds from the start of the recording."""

    start: float
    end: float
    title: str


def parse_chapters(raw: object) -> list[Chapter]:
    """
    Read a publisher chapter list as plain data, dropping anything unusable.

    Tolerant on purpose: this parses whatever an extractor or a stored resource happens to
    hold, and a malformed entry must cost that entry rather than the run.
    """
    if not isinstance(raw, list):
        return []
    chapters: list[Chapter] = []
    for entry in cast(list[object], raw):
        if not isinstance(entry, dict):
            continue
        fields = cast(dict[str, object], entry)
        title = fields.get("title")
        start = _seconds(fields.get("start_time"))
        if not isinstance(title, str) or not title.strip() or start is None:
            continue
        end = _seconds(fields.get("end_time"))
        chapters.append(
            Chapter(start=start, end=end if end is not None else start, title=title.strip())
        )
    return sorted(chapters, key=lambda chapter: chapter.start)


def _seconds(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def get_chapters(item: Item) -> list[Chapter]:
    """Read the publisher chapters recorded on an item, or an empty list."""
    return parse_chapters(cast(dict[str, object], item.extra or {}).get(CHAPTERS_KEY))


def has_timestamp_citations(body: str) -> bool:
    """Whether a body carries the citation spans a chapter boundary resolves against."""
    return _CITATION_PATTERN.search(body) is not None


def normalize_heading(text: str) -> str:
    """Collapse whitespace so a stored chapter title and a rendered heading compare equal."""
    return re.sub(r"\s+", " ", text).strip()


def _block_starts(body: str) -> list[int]:
    """Offsets where each Markdown block begins."""
    return [0, *(match.end() for match in _BLOCK_BREAK_PATTERN.finditer(body))]


def _block_text(body: str, starts: list[int], index: int) -> str:
    end = starts[index + 1] if index + 1 < len(starts) else len(body)
    return body[starts[index] : end]


def _insertion_offset(body: str, starts: list[int], citation_start: int) -> int:
    """
    Where a chapter heading goes, given the citation that anchors it.

    The heading belongs above the whole paragraph, not above the citation that closes it,
    so this walks back to the start of the paragraph's block — and then past any heading
    blocks immediately above it, because two headings with nothing between them say
    nothing. A chapter whose paragraph already has a heading over it takes the position
    above that heading, which is what keeps the skeleton clean when this runs on a body
    that has been through a heading stage already.
    """
    index = bisect.bisect_right(starts, citation_start) - 1
    while index > 0 and _HEADING_BLOCK_PATTERN.match(_block_text(body, starts, index - 1).strip()):
        index -= 1
    return starts[index]


def insert_chapter_headings_in_body(body: str, chapters: list[Chapter]) -> str:
    """
    Insert `## <title>` above the first paragraph that starts at or after each chapter.

    A chapter boundary that falls mid-paragraph goes above the NEXT paragraph: the words
    already being spoken belong to the chapter they started in, and splitting a paragraph
    would break the citation that anchors it.

    Two rules decide the awkward cases, and both are the same rule seen from either side.
    A chapter with no paragraph of its own — the next chapter resolves to the same
    paragraph — is DROPPED rather than inserted as an empty stretch. A heading is a promise
    that the words under it belong to that chapter, and the alternative, sliding the
    chapter down to the next free paragraph, quietly puts a title over prose from a later
    part of the recording. A heading with nothing under it is no better: the `##` skeleton
    becomes the index's section list, so an empty section is a timeline row that highlights
    nothing and an outline entry with nothing to summarize. A chapter starting after the
    last paragraph is dropped for the same reason.

    Idempotent: a chapter whose title is already a `##` heading is left alone, so a second
    pass over the same body inserts nothing.
    """
    if not body or not chapters:
        return body

    citations = list(_CITATION_PATTERN.finditer(body))
    if not citations:
        log.info("No timestamp citations to anchor %d publisher chapters to", len(chapters))
        return body

    existing = {
        normalize_heading(match.group("heading")) for match in _H2_LINE_PATTERN.finditer(body)
    }
    timestamps = [float(match.group("ts")) for match in citations]
    starts = _block_starts(body)

    insertions: list[tuple[int, str]] = []
    claimed: int | None = None
    for chapter in chapters:
        index = next((i for i, ts in enumerate(timestamps) if ts >= chapter.start), None)
        if index is None:
            log.info(
                "Chapter %r starts at %.0fs, after the last paragraph; leaving it out",
                chapter.title,
                chapter.start,
            )
            continue
        already_present = normalize_heading(chapter.title) in existing
        if index == claimed:
            if not already_present:
                log.info(
                    "Chapter %r has no paragraph of its own before the next chapter; "
                    "leaving it out",
                    chapter.title,
                )
            continue
        claimed = index
        if already_present:
            continue
        insertions.append(
            (_insertion_offset(body, starts, citations[index].start()), chapter.title)
        )

    if not insertions:
        return body

    pieces: list[str] = []
    cursor = 0
    for offset, title in insertions:
        offset = max(offset, cursor)
        pieces.append(body[cursor:offset])
        pieces.append(f"## {title}\n\n")
        cursor = offset
    pieces.append(body[cursor:])
    log.info("Inserted %d publisher chapters as section headings", len(insertions))
    return "".join(pieces)


def demote_nonchapter_headings_in_body(body: str, chapters: list[Chapter]) -> str:
    """
    Turn every `##` heading that is not a chapter title into a `###` heading.

    Titles are compared exactly, after whitespace normalization, so a model heading that
    happens to read like a chapter title keeps its level rather than being guessed at.
    """
    if not body or not chapters:
        return body
    titles = {normalize_heading(chapter.title) for chapter in chapters}

    def demote(match: re.Match[str]) -> str:
        if normalize_heading(match.group("heading")) in titles:
            return match.group(0)
        return "#" + match.group(0)

    return _H2_LINE_PATTERN.sub(demote, body)


def _fetch_publisher_chapters(url: str) -> list[dict[str, Any]]:
    """Ask yt-dlp for the chapter list, without downloading anything."""
    from yt_dlp import YoutubeDL

    # yt-dlp types its options as a TypedDict it does not export, so this stays untyped.
    ytdl_options: Any = {"quiet": True, "no_warnings": True, "skip_download": True}
    try:
        info = YoutubeDL(ytdl_options).extract_info(url, download=False)
    except Exception as error:
        # A source without chapters is the ordinary case, and a real extractor problem will
        # be reported by the download that follows this. Neither deserves a warning here.
        log.info("Could not read publisher chapters for %s: %s", url, error)
        return []
    raw: object = (info or {}).get("chapters")
    return [
        {"start_time": chapter.start, "end_time": chapter.end, "title": chapter.title}
        for chapter in parse_chapters(raw)
    ]


def attach_publisher_chapters(item: Item) -> bool:
    """
    Record the publisher's chapter list on a YouTube resource that has one.

    kash's stored source metadata does not carry chapters, so this is a second yt-dlp call.
    It is metadata-only — `skip_download`, a few seconds, no bytes on disk — and it runs
    before the space check, so nothing has been paid for if it fails.

    Chapters go in the resource metadata every later action hashes, unlike a view counter,
    because they are stable: a chapter list does not move on its own. The cost is that the
    first run after this lands sees a changed resource and redoes the pipeline once,
    speech-to-text included.

    The fetch deliberately ignores `--no-chapters`. If the flag also skipped the fetch,
    toggling it would flip the stored resource back and forth and buy a fresh paid
    transcription every time; instead the flag only decides whether the two chapter stages
    run.

    Returns whether anything was added, because kash's fetch has ALREADY written the item
    to disk by the time this runs — the caller must persist when this returns True.
    """
    if not item.url:
        return False
    extra = item.extra or {}
    if CHAPTERS_KEY in extra or extra.get("media_service") != "youtube":
        return False

    chapters = _fetch_publisher_chapters(item.url)
    if not chapters:
        return False
    item.extra = {**extra, CHAPTERS_KEY: chapters}
    log.info("Recorded %d publisher chapters for %s", len(chapters), item.url)
    return True


@kash_action(precondition=has_simple_text_body)
def insert_chapter_headings(item: Item) -> Item:
    """
    Insert the publisher's chapters as `##` section headings, anchored on timestamps.
    """
    if not item.body:
        raise InvalidInput(f"Item must have a body: {item}")
    return item.derived_copy(body=insert_chapter_headings_in_body(item.body, get_chapters(item)))


@kash_action(precondition=has_simple_text_body)
def demote_model_headings(item: Item) -> Item:
    """
    Demote every `##` heading that is not a publisher chapter title to `###`.
    """
    if not item.body:
        raise InvalidInput(f"Item must have a body: {item}")
    return item.derived_copy(body=demote_nonchapter_headings_in_body(item.body, get_chapters(item)))


## Tests


LEX_501_CHAPTERS: list[dict[str, Any]] = [
    {"start_time": 0.0, "end_time": 87.0, "title": "Episode highlight"},
    {"start_time": 87.0, "end_time": 176.0, "title": "Introduction"},
    {"start_time": 176.0, "end_time": 1094.0, "title": "Programming with AI agents"},
    {"start_time": 1094.0, "end_time": 1650.0, "title": "How software will change"},
    {"start_time": 1650.0, "end_time": 2241.0, "title": "AI impact on open source"},
    {"start_time": 2241.0, "end_time": 2825.0, "title": "Building Omarchy Linux distro"},
    {"start_time": 2825.0, "end_time": 3606.0, "title": "Vibe coding vs agentic engineering"},
    {"start_time": 3606.0, "end_time": 4224.0, "title": "The end of manual programming"},
    {"start_time": 4224.0, "end_time": 4950.0, "title": "Advice for programmers"},
    {"start_time": 4950.0, "end_time": 5506.0, "title": "Surviving Internet Hate"},
    {"start_time": 5506.0, "end_time": 6251.0, "title": "Programming setup for AI Agents"},
    {"start_time": 6251.0, "end_time": 7626.0, "title": "Obsessing about speed"},
    {"start_time": 7626.0, "end_time": 8465.0, "title": "Voice prompting vs typing"},
    {"start_time": 8465.0, "end_time": 9475.0, "title": "Best AI coding models"},
    {"start_time": 9475.0, "end_time": 10257.0, "title": "Best AI coding harnesses"},
    {"start_time": 10257.0, "end_time": 11428.0, "title": "AI video generation and filmmaking"},
    {"start_time": 11428.0, "end_time": 13115.0, "title": "Fatherhood"},
    {"start_time": 13115.0, "end_time": 13791.0, "title": "Linux will win the desktop"},
    {"start_time": 13791.0, "end_time": 14364.0, "title": "PewDiePie"},
    {"start_time": 14364.0, "end_time": 15737.0, "title": "Future of programming"},
    {"start_time": 15737.0, "end_time": 17634.0, "title": "Politics and immigration"},
    {
        "start_time": 17634.0,
        "end_time": 18338.0,
        "title": "Longevity, over-optimization, and fear of death",
    },
    {
        "start_time": 18338.0,
        "end_time": 18951.0,
        "title": "Eternal recurrence and future of human civization",
    },
]
"""
The 23 chapters YouTube publishes for Lex Fridman Podcast #501, as yt-dlp returns them.

Fetched once with a metadata-only extract and pasted here, so the check that the index
sees exactly the published sections never touches the network.
"""


def _paragraph(text: str, timestamp: float) -> str:
    """One citation-anchored paragraph, in the shape `normalize_timestamp_citations` leaves."""
    return (
        f"{text}\n"
        f'<span class="citation timestamp-link" data-src="resources/x.resource.yml" '
        f'data-timestamp="{timestamp:.2f}">'
        f'<a href="https://www.youtube.com/watch?v=x&amp;t={timestamp}s">{timestamp:.0f}</a>'
        "</span>"
    )


def _blocks(*blocks: str) -> str:
    return "\n\n".join(blocks) + "\n"


def _h2_lines(body: str) -> list[str]:
    return [line for line in body.splitlines() if line.startswith("## ")]


def _h3_lines(body: str) -> list[str]:
    return [line for line in body.splitlines() if line.startswith("### ")]


def test_chapter_headings_land_on_the_first_paragraph_at_or_after_each_start() -> None:
    """
    A citation's timestamp is the start of the paragraph it closes, so a chapter boundary
    resolves to the first paragraph that begins at or after it. A boundary that falls
    mid-paragraph therefore lands on the NEXT paragraph, and the words already being spoken
    stay with the chapter they started in.
    """
    body = _blocks(
        _paragraph("Cold open.", 4.5),
        _paragraph("Still the cold open.", 31.5),
        _paragraph("Now the introduction.", 90.0),
        _paragraph("The introduction keeps going.", 120.0),
        _paragraph("On to the main topic.", 200.0),
    )
    chapters = parse_chapters(
        [
            {"start_time": 0, "end_time": 87, "title": "Episode highlight"},
            {"start_time": 87, "end_time": 130, "title": "Introduction"},
            # 130 is inside the paragraph anchored at 120, which runs to 200.
            {"start_time": 130, "end_time": 400, "title": "Main topic"},
        ]
    )

    result = insert_chapter_headings_in_body(body, chapters)

    assert _h2_lines(result) == [
        "## Episode highlight",
        "## Introduction",
        "## Main topic",
    ]
    assert result.startswith("## Episode highlight\n\nCold open.")
    assert "## Introduction\n\nNow the introduction." in result
    assert "## Main topic\n\nOn to the main topic." in result
    assert "## Main topic\n\nThe introduction keeps going." not in result
    # Nothing but the heading blocks was added: take them back out and the bytes match.
    assert re.sub(r"^## .*\n\n", "", result, flags=re.MULTILINE) == body


def test_a_source_without_chapters_leaves_the_body_byte_identical() -> None:
    """Both stages have to be invisible on a source the publisher never chaptered."""
    body = _blocks(
        "## A model heading",
        _paragraph("One.", 1.0),
        "## Another model heading",
        _paragraph("Two.", 30.0),
    )

    assert insert_chapter_headings_in_body(body, []) == body
    assert demote_nonchapter_headings_in_body(body, []) == body


def test_running_the_insertion_twice_inserts_nothing_new() -> None:
    body = _blocks(
        _paragraph("Cold open.", 4.5),
        _paragraph("Now the introduction.", 90.0),
    )
    chapters = parse_chapters(
        [
            {"start_time": 0, "end_time": 87, "title": "Episode highlight"},
            {"start_time": 87, "end_time": 176, "title": "Introduction"},
        ]
    )

    once = insert_chapter_headings_in_body(body, chapters)
    assert _h2_lines(once) == ["## Episode highlight", "## Introduction"]
    assert insert_chapter_headings_in_body(once, chapters) == once


def test_demotion_lowers_the_model_headings_and_leaves_the_chapters_alone() -> None:
    body = _blocks(
        "# Episode title",
        "## Episode highlight",
        "##   The Revolutionary Moment in AI  ",
        _paragraph("One.", 1.0),
        "## Introduction",
        "### Already a sub-heading",
        "## Personal Philosophy on Risk",
        _paragraph("Two.", 90.0),
    )
    chapters = parse_chapters(
        [
            {"start_time": 0, "end_time": 87, "title": "Episode highlight"},
            {"start_time": 87, "end_time": 176, "title": " Introduction "},
        ]
    )

    result = demote_nonchapter_headings_in_body(body, chapters)

    assert _h2_lines(result) == ["## Episode highlight", "## Introduction"]
    # Only the level changes; the heading text, odd spacing and all, is left as it was.
    assert _h3_lines(result) == [
        "###   The Revolutionary Moment in AI  ",
        "### Already a sub-heading",
        "### Personal Philosophy on Risk",
    ]
    # The `#` title is not part of the section skeleton and is not touched.
    assert result.splitlines()[0] == "# Episode title"
    # The chapter titles matched despite the stored padding, and nothing else moved.
    assert result.replace("###", "##") == body.replace("###", "##")


def test_a_chapter_with_no_paragraph_of_its_own_is_left_out() -> None:
    """
    Two chapters resolving to the same paragraph would mean two headings with nothing
    between them, and a section the index reports with no units in it.
    """
    body = _blocks(_paragraph("One.", 1.0), _paragraph("Two.", 300.0))
    chapters = parse_chapters(
        [
            {"start_time": 0, "title": "Opening"},
            {"start_time": 100, "title": "A stretch nobody spoke in"},
            {"start_time": 200, "title": "Still nobody"},
        ]
    )

    result = insert_chapter_headings_in_body(body, chapters)

    assert _h2_lines(result) == ["## Opening", "## A stretch nobody spoke in"]
    assert "## Still nobody" not in result


def test_a_chapter_that_starts_after_the_last_paragraph_is_left_out() -> None:
    body = _blocks(_paragraph("Only paragraph.", 1.0))
    chapters = parse_chapters(
        [
            {"start_time": 0, "title": "Opening"},
            {"start_time": 500, "title": "An outro nobody transcribed"},
        ]
    )

    assert _h2_lines(insert_chapter_headings_in_body(body, chapters)) == ["## Opening"]


def test_a_chapter_goes_above_a_heading_that_already_introduces_its_paragraph() -> None:
    """Inserting between a heading and the prose it introduces would orphan the heading."""
    body = _blocks("## A model heading", _paragraph("One.", 1.0))
    chapters = parse_chapters([{"start_time": 0, "title": "Opening"}])

    result = insert_chapter_headings_in_body(body, chapters)

    assert result.startswith("## Opening\n\n## A model heading\n\nOne.")


def test_the_index_counts_exactly_the_published_chapters_as_sections() -> None:
    """
    The whole point of demoting rather than replacing: `transcript_index` reads only `##`,
    so the index, the outline chunking and the timeline all see the publisher's 23 sections
    while every model heading survives underneath as a `###`.
    """
    from deep_transcribe.transcript_index import build_transcript_index

    chapters = parse_chapters(LEX_501_CHAPTERS)
    assert len(chapters) == 23

    # Three paragraphs per chapter, each introduced by a heading, which is the shape the
    # real run produces: the windowed stage puts out roughly ten headings per chapter.
    blocks: list[str] = []
    for chapter in chapters:
        for offset in (1.0, 20.0, 40.0):
            blocks.append(f"## Model heading at {chapter.start + offset:.0f}")
            blocks.append(_paragraph("Some spoken words here.", chapter.start + offset))
    body = "\n\n".join(blocks) + "\n"

    sectioned = demote_nonchapter_headings_in_body(
        insert_chapter_headings_in_body(body, chapters), chapters
    )

    assert _h2_lines(sectioned) == [f"## {chapter.title}" for chapter in chapters]
    assert len(_h3_lines(sectioned)) == 69

    index = build_transcript_index(sectioned, duration=18951.0)

    assert len(index.sections) == 23
    assert [section.heading for section in index.sections] == [c.title for c in chapters]
    # Every section owns paragraphs, which is what "no empty stretches" means downstream.
    assert {unit.section for unit in index.units} == {f"sec{i}" for i in range(23)}


def test_chapters_are_read_once_and_only_for_youtube_sources() -> None:
    from unittest.mock import patch

    from kash.model import Format, ItemType
    from kash.utils.common.url import Url

    fetched: list[str] = []

    def fake_fetch(url: str) -> list[dict[str, Any]]:
        fetched.append(url)
        return [{"start_time": 0.0, "end_time": 10.0, "title": "Opening"}]

    def resource(url: str, **extra: object) -> Item:
        return Item(type=ItemType.resource, format=Format.url, url=Url(url), extra=dict(extra))

    youtube = resource("https://www.youtube.com/watch?v=abcdefghijk", media_service="youtube")
    local = resource("file:///tmp/interview.mp4")
    page = resource("https://example.com/article", media_service="vimeo")

    with patch(f"{__name__}._fetch_publisher_chapters", fake_fetch):
        assert attach_publisher_chapters(youtube) is True
        # Already stored: refetching would rewrite the resource every run.
        assert attach_publisher_chapters(youtube) is False
        assert attach_publisher_chapters(local) is False
        assert attach_publisher_chapters(page) is False

    assert fetched == ["https://www.youtube.com/watch?v=abcdefghijk"]
    assert get_chapters(youtube) == [Chapter(start=0.0, end=10.0, title="Opening")]
    assert get_chapters(local) == []


def test_malformed_chapter_entries_cost_the_entry_and_not_the_run() -> None:
    chapters = parse_chapters(
        [
            {"start_time": 60, "end_time": 90, "title": "Second"},
            {"start_time": 0, "end_time": 60, "title": "First"},
            {"start_time": 10, "title": "   "},
            {"start_time": "nope", "title": "Bad start"},
            {"title": "No start at all"},
            "not a mapping",
        ]
    )

    assert [chapter.title for chapter in chapters] == ["First", "Second"]
    assert parse_chapters(None) == []
    assert parse_chapters({"chapters": []}) == []
