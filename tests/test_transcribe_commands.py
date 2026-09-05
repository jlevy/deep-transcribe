# pyright: reportPrivateUsage=false

import logging
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

import pytest
from kash.model import Item, ItemType

from deep_transcribe import transcribe_commands
from deep_transcribe.transcribe_commands import _media_source_locator, _prepare_source_item
from deep_transcribe.transcribe_options import TranscribeOptions
from deep_transcribe.transcription_metadata import get_processing_instructions


def test_local_media_uses_file_url_without_changing_remote_sources() -> None:
    with TemporaryDirectory() as temp_dir:
        source_path = Path(temp_dir) / "recording.mp4"
        source_path.write_bytes(b"video")

        local_locator = _media_source_locator(str(source_path))

    assert local_locator == f"file://{source_path.resolve()}"
    assert _media_source_locator("https://example.com/interview") == (
        "https://example.com/interview"
    )


def test_local_media_url_registration_does_not_copy_the_source() -> None:
    from kash.exec import kash_runtime, prepare_action_input
    from kash.model import Format, ItemType

    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_path = temp_path / "recording.mp4"
        source_path.write_bytes(b"video")
        workspace_path = temp_path / "workspace"

        with kash_runtime(workspace_path):
            item = prepare_action_input(_media_source_locator(str(source_path))).items[0]

        assert item.type is ItemType.resource
        assert item.format is Format.url
        assert item.url == f"file://{source_path.resolve()}"
        assert not list(workspace_path.rglob("*.mp4"))


@pytest.mark.filterwarnings("ignore::pytest.PytestUnknownMarkWarning")
def test_remote_media_preparation_enriches_fresh_and_incomplete_cached_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from kash.exec import kash_runtime
    from kash.kits.media.media_services.youtube import YouTube
    from kash.model import Format
    from kash.utils.common.url import Url
    from kash.workspaces import current_ws

    source_url = "https://www.youtube.com/watch?v=abcdefghijk"
    extractor_result: dict[str, Any] = {
        "id": "abcdefghijk",
        "webpage_url": source_url,
        "title": "Hotel Check In - SNL",
        "description": "An SNL hotel sketch with two guests.",
        "upload_date": "20171015",
        "channel_url": "https://www.youtube.com/channel/example",
        "view_count": 100,
        "duration": 266,
    }

    def fake_extract_info(_self: YouTube, _url: Url) -> dict[str, Any]:
        return extractor_result

    monkeypatch.setattr(YouTube, "_extract_info", fake_extract_info)

    with TemporaryDirectory() as temp_dir, kash_runtime(Path(temp_dir) / "workspace"):
        item = _prepare_source_item(source_url)
        assert item.type is ItemType.resource
        assert item.format is Format.url
        assert item.title == "Hotel Check In - SNL"
        assert item.description == "An SNL hotel sketch with two guests."
        assert item.extra is not None
        assert item.extra["media_service"] == "youtube"
        assert str(item.extra["upload_date"]) == "2017-10-15"
        assert item.extra["channel_url"] == "https://www.youtube.com/channel/example"

        item.title = "Cached webpage title"
        item.extra = {}
        current_ws().save(item, overwrite=True)
        enriched_item = _prepare_source_item(source_url)

    assert enriched_item.title == "Hotel Check In - SNL"
    assert enriched_item.extra is not None
    assert enriched_item.extra["media_service"] == "youtube"


def test_processing_instructions_bypass_raw_and_formatting_cache_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from kash import workspaces

    instructions = "Keep the synopsis compact and the outline chronological."
    source = Item(
        type=ItemType.resource,
        title="Fixture",
        extra={"transcription": {"processing_instructions": instructions}},
        store_path="resources/fixture.resource.yml",
    )
    raw_result = Item(type=ItemType.doc, title="Fixture", extra={"transcription": {}})
    observed: dict[str, object] = {}
    persisted_instructions: list[str | None] = []

    class FakeWorkspace:
        base_dir: Path = Path("/tmp/fake-workspace")

        def save(self, _item: Item, *, overwrite: bool) -> None:
            assert overwrite is True

    def fake_persist(item: Item, _workspace: object) -> None:
        persisted_instructions.append(get_processing_instructions(item))

    def fake_transcribe(item: Item, **_kwargs: object) -> Item:
        observed["raw_instructions"] = get_processing_instructions(item)
        return raw_result

    def fake_process(
        item: Item,
        _options: TranscribeOptions,
        *,
        processing_instructions: str | None,
        **_late_inputs: object,
    ) -> Item:
        observed["formatting_instructions"] = get_processing_instructions(item)
        observed["overview_instructions"] = processing_instructions
        return item

    monkeypatch.setattr(transcribe_commands, "_transcribe_raw", fake_transcribe)
    monkeypatch.setattr(transcribe_commands, "_process_transcript", fake_process)
    monkeypatch.setattr(transcribe_commands, "persist_item_metadata", fake_persist)
    monkeypatch.setattr(workspaces, "current_ws", lambda: FakeWorkspace())

    result = transcribe_commands.transcribe_with_options(source, TranscribeOptions.basic())

    assert result is raw_result
    assert observed == {
        "raw_instructions": None,
        "formatting_instructions": None,
        "overview_instructions": instructions,
    }
    assert persisted_instructions == [None, instructions]
    assert get_processing_instructions(source) == instructions


def test_processing_instructions_get_a_distinct_overview_cache_boundary() -> None:
    from inspect import unwrap

    instructions = "Make the synopsis shorter."
    item = Item(
        type=ItemType.doc,
        body="Transcript body.",
        store_path="docs/sectioned.doc.md",
    )

    result = unwrap(transcribe_commands._attach_late_inputs)(
        item,
        processing_instructions=instructions,
    )

    assert result is not item
    assert result.store_path is None
    assert get_processing_instructions(item) is None
    assert get_processing_instructions(result) == instructions


def test_hints_leave_no_trace_for_the_stages_above_the_boundary() -> None:
    """
    The whole segment-hint design rests on this: editing a hint must not disturb
    transcription, speaker correction, paragraph formatting or section headings.

    Those stages key their cache on the item, so the test is that an item with hints
    stripped is indistinguishable from one that never carried any. If this ever fails,
    the symptom is only that reruns "feel slow", which nobody files as a bug.
    """
    from deep_transcribe.transcription_metadata import (
        get_segment_hints,
        remove_segment_hints,
        set_segment_hints,
    )

    def make() -> Item:
        return Item(
            type=ItemType.doc,
            body="Transcript body.",
            extra={"transcription": {"key_terms": ["Omarchy"], "speaker_roster": ["Alice"]}},
        )

    never_had_hints = make()
    carried_hints = make()
    hints = {"segments": [{"at": "0:00 - 3:14", "purpose": "teaser"}]}
    set_segment_hints(carried_hints, hints)

    assert carried_hints.extra != never_had_hints.extra
    returned = remove_segment_hints(carried_hints)

    assert returned == hints
    assert carried_hints.extra == never_had_hints.extra
    assert get_segment_hints(carried_hints) is None
    # Removing from an item that never had them is a no-op, not a mutation.
    before = dict(never_had_hints.extra or {})
    assert remove_segment_hints(never_had_hints) is None
    assert never_had_hints.extra == before


def test_late_inputs_carry_both_instructions_and_hints() -> None:
    from inspect import unwrap

    from deep_transcribe.transcription_metadata import get_segment_hints

    item = Item(type=ItemType.doc, body="Transcript body.", store_path="docs/sectioned.doc.md")

    result = unwrap(transcribe_commands._attach_late_inputs)(  # noqa: SLF001
        item,
        processing_instructions="Keep it short.",
        segment_hints='segments:\n- at: "0:00 - 3:14"\n  purpose: teaser\n',
    )

    assert get_processing_instructions(result) == "Keep it short."
    hints = get_segment_hints(result)
    assert isinstance(hints, dict)
    assert hints["segments"][0]["purpose"] == "teaser"
    # The source item is untouched, so its own identity is unchanged.
    assert get_segment_hints(item) is None


def test_clearing_a_hint_reaches_the_stored_resource_on_disk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Drive the real CLI path: `--segments none` must delete the key from the resource file.

    Hints and instructions are sticky by design — they are written back onto the stored
    source so a later run without the flag still honors them — so a clear only counts if
    the stored YAML in the workspace loses the key. An in-memory removal would leave the
    next run reading the hint straight back off disk while every unit test still passed.
    """
    from kash.model import Format
    from kash.utils.common.url import Url
    from kash.workspaces import current_ws

    from deep_transcribe.cli_main import build_parser, build_transcription_metadata
    from deep_transcribe.transcription_metadata import set_segment_hints

    stored_path: list[Path] = []
    before_clear: list[str] = []

    def fake_prepare(_source: str) -> Item:
        workspace = current_ws()
        item = Item(
            type=ItemType.resource,
            format=Format.url,
            url=Url("https://example.com/video"),
            title="Fixture",
            extra={"transcription": {"speaker_roster": ["Host", "Guest"]}},
        )
        set_segment_hints(item, {"segments": [{"at": "0:00:00 - 0:01:49", "purpose": "teaser"}]})
        workspace.save(item)
        path = workspace.base_dir / str(item.store_path)
        stored_path.append(path)
        before_clear.append(path.read_text())
        return item

    def fake_transcribe(item: Item, *_args: object, **_kwargs: object) -> Item:
        return item

    def fake_format(_result: Item, _base_dir: Path, **_kwargs: object) -> tuple[Path, Path]:
        return Path("transcript.md"), Path("transcript.html")

    monkeypatch.setattr(transcribe_commands, "_prepare_source_item", fake_prepare)
    monkeypatch.setattr(transcribe_commands, "transcribe_with_options", fake_transcribe)
    monkeypatch.setattr(transcribe_commands, "format_results", fake_format)

    args = build_parser().parse_args(["--segments", "none", "https://example.com/video"])

    with TemporaryDirectory() as temp_dir:
        transcribe_commands.run_transcription(
            Path(temp_dir),
            "https://example.com/video",
            TranscribeOptions.basic(),
            "en",
            metadata=build_transcription_metadata(args),
        )
        after = stored_path[0].read_text()

    assert "purpose: teaser" in before_clear[0]
    assert "segments" not in after
    assert "speaker_roster" in after


DETECTED_CLIP_START = 4.56
DETECTED_CLIP_END = 108.55
"""The span the detector found on the measured recording, used as the fixed detection."""


def _fix_the_detection(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Make detection return the clip measured on the real recording, always.

    These tests say nothing about the detector and everything about what is done with
    what it found, and a fixed clip keeps them offline and deterministic.
    """
    from deep_transcribe import preview_detection
    from deep_transcribe.preview_detection import PreviewClip

    clip = PreviewClip(
        start=DETECTED_CLIP_START, end=DETECTED_CLIP_END, units=6, echoed_fraction=0.83
    )

    def fixed_detection(*_args: object, **_kwargs: object) -> PreviewClip:
        return clip

    monkeypatch.setattr(preview_detection, "detect_preview_clip", fixed_detection)


def _transcript_item() -> Item:
    from kash.model import Format

    return Item(
        type=ItemType.doc,
        format=Format.md_html,
        title="A recording",
        body="The best moments, first. <span data-timestamp='4.56' />\n",
    )


def _own_workspace(tmp_path: Path) -> Path:
    """
    A workspace directory whose name no other test shares.

    kash registers workspaces by directory name, so two tests both using `tmp_path /
    "workspace"` resolve `current_ws()` to whichever one registered first — and then one
    test reads the suggestion file the other wrote. Measured while writing these: the
    "no coverage" cases passed against a deliberately broken fix because the file was
    already sitting in a workspace from an earlier test.
    """
    return tmp_path / f"ws-{tmp_path.name}"


def _suggestion_path(workspace_path: Path) -> Path:
    """Where the suggestion goes, checked against the workspace the runtime actually used."""
    from kash.workspaces import current_ws

    from deep_transcribe.transcribe_commands import SUGGESTED_SEGMENTS_NAME

    base_dir = current_ws().base_dir
    assert base_dir.resolve() == workspace_path.resolve(), (
        f"the runtime used workspace {base_dir}, not {workspace_path}"
    )
    return base_dir / SUGGESTED_SEGMENTS_NAME


def _run_pipeline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, hints: object) -> Path:
    """
    Run the real processing pipeline the way a run with hints reaches the suggestion.

    Driven through `_process_transcript` rather than the suggestion alone, because the
    stage strips the hints off the item on the way in and `_attach_late_inputs` puts them
    back: a check that only ever saw a hand-assembled item could pass while the real path
    saw nothing. Every option is off, so nothing here calls a model.

    Returns the path the suggestion would occupy, so a caller can assert either way.
    """
    from kash.exec import kash_runtime

    _fix_the_detection(monkeypatch)
    workspace_path = _own_workspace(tmp_path)

    with kash_runtime(workspace_path):
        transcribe_commands._process_transcript(
            _transcript_item(),
            TranscribeOptions.basic(),
            processing_instructions=None,
            segment_hints=hints,
        )
        return _suggestion_path(workspace_path)


ADOPTED_HINTS = {"segments": [{"at": "0:00:04 - 0:01:49", "purpose": "teaser"}]}
"""The suggestion for the detected clip, as the tool wrote it and the user adopted it."""


def test_a_segment_the_user_already_marked_is_not_suggested_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """
    The user ran the tool, adopted the suggestion, and reran with `--segments`. Proposing
    the same span again asks them to adopt what they already adopted, and teaches them to
    ignore the message that will matter the next time detection finds something new.

    The adopted span is the one the tool wrote for this clip, rounded outward to whole
    seconds, which is why the comparison cannot be an exact one.

    The log line is part of the behaviour, not decoration: silence here is also what a
    version that never looked at the hints produces, and those two are not the same thing
    — one of them goes on to suggest a genuinely new detection.
    """
    with caplog.at_level(logging.INFO, logger="deep_transcribe.transcribe_commands"):
        path = _run_pipeline(tmp_path, monkeypatch, hints=ADOPTED_HINTS)

    assert not path.exists(), f"re-offered a segment already marked: {path.read_text()}"
    said = [r.getMessage() for r in caplog.records if r.name == transcribe_commands.__name__]
    assert any("already mark" in message for message in said), (
        f"nothing says the clip was found already marked in the hints in effect: {said}"
    )


def test_a_marked_segment_carried_only_on_the_item_is_not_suggested_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    The same check, reading the other place hints live: on the item, where the stage below
    the cache boundary puts them for the analysis to read. Whichever of the two a caller
    holds, an adopted segment must not come back as a proposal.
    """
    from kash.exec import kash_runtime

    from deep_transcribe.transcription_metadata import set_segment_hints

    _fix_the_detection(monkeypatch)
    item = _transcript_item()
    set_segment_hints(item, ADOPTED_HINTS)
    workspace_path = _own_workspace(tmp_path)

    with kash_runtime(workspace_path):
        transcribe_commands._suggest_segments(item, None)
        path = _suggestion_path(workspace_path)

    assert not path.exists(), f"re-offered a segment already marked: {path.read_text()}"


@pytest.mark.parametrize(
    "hints",
    [
        pytest.param(
            {"segments": [{"at": "1:00:00 - 1:02:30", "purpose": "promo"}]},
            id="a_hint_somewhere_else",
        ),
        pytest.param(
            {"segments": [{"at": "0:00:04 - 0:00:30", "purpose": "teaser"}]},
            id="a_hint_that_stops_short",
        ),
    ],
)
def test_hints_that_do_not_cover_the_clip_still_get_a_suggestion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hints: dict[str, Any]
) -> None:
    """
    Marking an ad read, or catching only the first paragraph of the reel, says nothing
    about the rest of the opening. Those runs still want the draft.
    """
    path = _run_pipeline(tmp_path, monkeypatch, hints=hints)

    assert path.exists()
    text = path.read_text()
    assert "0:00:04 - 0:01:49" in text
    assert "purpose: teaser" in text


def test_a_run_with_no_hints_at_all_gets_a_suggestion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The first run, which is what the detector is there for."""
    path = _run_pipeline(tmp_path, monkeypatch, hints=None)

    assert path.exists()
    assert "0:00:04 - 0:01:49" in path.read_text()


def _speaker_label(speaker_id: int, name: str) -> str:
    return f'<span class="speaker-label" data-speaker-id="{speaker_id}">**{name}:**</span>'


def _exchange_with_back_channels() -> Item:
    """
    A five-turn exchange in the shape the transcribe stage hands downstream, two of whose
    turns are nothing but an acknowledgement.

    Taken from the measured recording, where turns like these run to several hundred.
    """
    from kash.model import Format

    body = "\n\n".join(
        f'{_speaker_label(speaker_id, name)} <span data-timestamp="{timestamp}">{text}</span>'
        for speaker_id, name, timestamp, text in [
            (0, "DHH", "313.84", "Everything turned from, like, this glamour, the pop."),
            (1, "Lex Fridman", "314.76", "Great regression."),
            (0, "DHH", "314.77", "So"),
            (1, "Lex Fridman", "314.83", "They niche in, you know, eternal recurrence."),
            (0, "DHH", "320.10", "Mhmm."),
        ]
    )
    return Item(
        type=ItemType.doc,
        format=Format.html,
        title="A recording",
        body=body + "\n",
    )


def _body_reaching_backfill(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, options: TranscribeOptions
) -> str:
    """
    Run the real formatting pipeline and return the body `backfill_timestamps` is handed.

    Only that one stage is replaced, and only because it reads timestamps back off the
    media resource the doc was derived from, which a synthetic item has not got. Every
    other stage runs for real: `break_into_paragraphs` skips itself on a doc this small,
    so nothing here calls a model.

    Reading the body at that point is what pins the fold's position in the pipeline — a
    fold that happened after backfill would leave the timestamps it is supposed to remove.
    """
    import kash.kits.media.actions.transcribe.backfill_timestamps as backfill_module
    from kash.exec import kash_runtime
    from kash.model import Format

    seen: list[str] = []

    def fake_backfill(item: Item, **_kwargs: object) -> Item:
        seen.append(item.body or "")
        return item.derived_copy(type=ItemType.doc, format=Format.md_html)

    monkeypatch.setattr(backfill_module, "backfill_timestamps", fake_backfill)

    with kash_runtime(_own_workspace(tmp_path)):
        transcribe_commands._process_transcript(
            _exchange_with_back_channels(),
            options,
            processing_instructions=None,
            segment_hints=None,
        )

    assert len(seen) == 1, f"expected one backfill call, got {len(seen)}"
    return seen[0]


def _turn_count(body: str) -> int:
    """Speaker turns, counted the way the rendered page shows them: one per labelled paragraph."""
    import re

    return len(re.findall(r"(?:\A|\n\s*\n)\s*\*\*[^*\n]+:\*\*", body))


def _paragraph_holding(body: str, text: str) -> str:
    """
    The paragraph containing `text`, which is the unit that matters here.

    The aside is appended to the paragraph, not to its last line: saving the item runs the
    Markdown formatter, which puts a sentence on a line of its own. Same paragraph either
    way, and one timestamp chip either way, so the check is paragraph membership.
    """
    import re

    holders = [p for p in re.split(r"\n[ \t]*\n", body) if text in p]
    assert len(holders) == 1, f"expected one paragraph holding {text!r}, got {len(holders)}"
    return holders[0]


def test_the_formatting_pipeline_folds_back_channel_turns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two of the five turns carry no content, and by default they stop being turns."""
    body = _body_reaching_backfill(tmp_path, monkeypatch, TranscribeOptions(format=True))

    assert _turn_count(body) == 3
    assert "[DHH: So]" in _paragraph_holding(body, "Great regression.")
    assert "[DHH: Mhmm.]" in _paragraph_holding(body, "eternal recurrence.")


def test_keeping_back_channels_leaves_every_turn_standing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--keep-backchannel` reaches the pipeline, and nothing is folded."""
    body = _body_reaching_backfill(
        tmp_path, monkeypatch, TranscribeOptions(format=True, keep_back_channel=True)
    )

    assert _turn_count(body) == 5
    assert "[DHH: Mhmm.]" not in body
    assert "**DHH:** Mhmm." in body


REPORT_SOURCE_URL = "https://example.com/report-recording"
"""The source the reported item claims, so the re-export lookup has something to match."""


def _reported_body() -> str:
    """
    A final item's body, small but shaped like the real one.

    Every count the report prints is read out of this body, so it carries the structures
    that matter and nothing else: three `##` sections, six labelled turns anchored by the
    citation spans the pipeline emits, an outline block, a frame capture, and one name
    spelled two ways. The spelling pair is the planted measurement — Omarchy three times
    and Omachi twice is the mistake the real recording made about sixty times, and it is
    invisible without this list.
    """

    def turn(label: str, ts: str, text: str) -> str:
        chip = (
            f'<span class="citation timestamp-link" data-src="r.yml" '
            f'data-timestamp="{ts}">{ts}</span>'
        )
        return f"**{label}:** {text} {chip}\n\n"

    return (
        '<div class="transcript-outline" style="x">\n\n'
        "- **Opening**\n  - a point\n- **The setup**\n  - another\n\n"
        '<div class="original">\n\n</div>\n\n'
        "## Opening\n\n"
        + turn("Ada", "12.50", "Welcome. We are talking about Omarchy today.")
        + turn("Grace", "48.00", "I have used Omarchy for a while.")
        + "## The setup\n\n"
        + turn("Ada", "600.25", "Tell me how Omachi installs.")
        + turn("Grace", "900.00", "Omachi is the spelling on the box.")
        + '<img class="frame-capture" src="frames/f1.jpg" alt="Frame at 900.0 seconds">\n\n'
        + "## The tooling\n\n"
        + turn("Ada", "1200.00", "So Omarchy is a Linux distribution.")
        + turn("Grace", "1500.00", "Linux, yes.")
    )


def _reported_item() -> Item:
    """The item a finished run would hand `format_results`, with its analysis attached."""
    from kash.model import Format
    from kash.utils.common.url import Url

    from deep_transcribe.transcription_metadata import set_segment_hints

    item = Item(
        type=ItemType.doc,
        format=Format.md_html,
        title="A reported recording",
        url=Url(REPORT_SOURCE_URL),
        body=_reported_body(),
        # The density is per hour of source, and the extractor's duration is where that
        # comes from; half an hour makes the arithmetic checkable by eye.
        extra={"duration": 1800},
    )
    item.extra = dict(item.extra or {})
    item.extra["transcription"] = {
        "concepts": [
            {"name": "Omarchy", "theme": "Tooling", "mentions": ["12.50", "1200.00"]},
            {"name": "Linux", "theme": "Tooling", "mentions": ["1500.00"]},
            {"name": "Installation", "theme": "Setup", "mentions": ["600.25"]},
            {"name": "An aside", "mentions": ["48.00"]},
        ]
    }
    set_segment_hints(item, {"segments": [{"at": "0:00:00 - 0:01:00", "purpose": "teaser"}]})
    return item


def test_the_report_counts_what_the_final_item_actually_holds() -> None:
    """
    The report over a realistic final item, field by field.

    Each number here is one the agent reading the report acts on, so each is pinned rather
    than smoke-tested: a report that silently counted zero sections would still print.
    """
    from deep_transcribe.transcript_report import build_transcript_report

    report = build_transcript_report(_reported_item())

    assert [h.title for h in report.headings] == ["Opening", "The setup", "The tooling"]
    # The first citation under each heading is where that section starts.
    assert [h.start for h in report.headings] == [12.50, 600.25, 1200.00]
    assert report.duration == 1800.0
    # Three sections in half an hour.
    assert report.headings_per_hour == 6.0

    assert report.outline_entries == 2

    assert [(t.name, t.concepts) for t in report.themes] == [("Tooling", 2), ("Setup", 1)]
    assert report.unthemed_concepts == 1

    assert [(s.label, s.turns) for s in report.speakers] == [("Ada", 3), ("Grace", 3)]

    assert len(report.segments) == 1
    segment = report.segments[0]
    assert segment.purpose == "teaser"
    assert (segment.start, segment.end) == (0.0, 60.0)
    assert segment.suppressed is True
    # The 12.50 and 48.00 turns fall inside the first minute; 600.25 onward do not.
    assert segment.units == 2

    assert report.frames_kept == 1


def test_the_report_surfaces_one_name_spelled_two_ways() -> None:
    """
    The planted pair. Choosing `--key-term` values is the reason this list exists, so the
    variants have to appear with their counts and the ordinary words must not crowd them out.
    """
    from deep_transcribe.transcript_report import build_transcript_report

    report = build_transcript_report(_reported_item())
    counts = {entry.token: entry.count for entry in report.spellings}

    assert counts["Omarchy"] == 3
    assert counts["Omachi"] == 2
    assert counts["Linux"] == 2
    for ordinary in ("Welcome", "Tell", "So"):
        assert ordinary not in counts


def test_the_report_text_renders_every_section() -> None:
    """A report an agent reads is the text, not the dataclass."""
    from deep_transcribe.transcript_report import build_transcript_report, format_report_text

    text = format_report_text(build_transcript_report(_reported_item()))

    assert "headings 3 (6.0/h)" in text
    assert "outline 2 entries" in text
    assert "themes 2 (1 concepts unthemed)" in text
    assert "segments 1" in text
    assert "teaser" in text and "suppressed" in text
    assert "speakers 2" in text
    assert "frames 1 kept" in text
    assert "Omarchy" in text and "Omachi" in text


def test_the_json_report_carries_the_same_counts() -> None:
    """`--json` folds this dict in, so its shape is what an agent parses."""
    from deep_transcribe.transcript_report import build_transcript_report

    payload = build_transcript_report(_reported_item()).to_json_dict()

    assert payload["headings"]["count"] == 3
    assert payload["headings"]["per_hour"] == 6.0
    assert payload["outline"]["entries"] == 2
    assert payload["themes"]["count"] == 2
    assert payload["themes"]["unthemed_concepts"] == 1
    assert payload["segments"][0]["at"] == "0:00:00 - 0:01:00"
    assert payload["frames"]["kept"] == 1
    spellings = {row["token"]: row["count"] for row in payload["spellings"]}
    assert spellings["Omarchy"] == 3


def test_a_run_asked_for_a_report_describes_the_item_it_exported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    A normal run has to build the report from the item it just handed `format_results`.

    Fetching, transcription and rendering are faked because none of them is the point, but
    the seam under test is the real one: a run that reports on the source it started from,
    or on nothing at all, would still print a plausible-looking report. The last assertion
    is the other half — without the flag a run stays exactly as cheap as it was.
    """
    from kash.model import Format
    from kash.utils.common.url import Url
    from kash.workspaces import current_ws

    exported: list[Item] = []

    def fake_prepare(_source: str) -> Item:
        item = Item(
            type=ItemType.resource,
            format=Format.url,
            url=Url(REPORT_SOURCE_URL),
            title="Fixture",
        )
        current_ws().save(item)
        return item

    def fake_transcribe(_item: Item, *_args: object, **_kwargs: object) -> Item:
        return _reported_item()

    def fake_format(result: Item, _base_dir: Path, **_kwargs: object) -> tuple[Path, Path]:
        exported.append(result)
        return Path("transcript.md"), Path("transcript.html")

    monkeypatch.setattr(transcribe_commands, "_prepare_source_item", fake_prepare)
    monkeypatch.setattr(transcribe_commands, "transcribe_with_options", fake_transcribe)
    monkeypatch.setattr(transcribe_commands, "format_results", fake_format)

    ws_root = _own_workspace(tmp_path)
    outputs = transcribe_commands.run_transcription(
        ws_root,
        REPORT_SOURCE_URL,
        TranscribeOptions.basic(),
        "en",
        report=True,
    )

    assert len(exported) == 1
    report = outputs.report
    assert report is not None, "a run asked for a report came back without one"
    # The exported item's own sections, not the source resource's (which has none).
    assert [heading.title for heading in report.headings] == [
        "Opening",
        "The setup",
        "The tooling",
    ]
    assert [(theme.name, theme.concepts) for theme in report.themes] == [
        ("Tooling", 2),
        ("Setup", 1),
    ]

    plain = transcribe_commands.run_transcription(
        ws_root,
        REPORT_SOURCE_URL,
        TranscribeOptions.basic(),
        "en",
    )
    assert plain.report is None


def test_pipeline_stage_order_covers_the_stages_the_pipeline_runs() -> None:
    """
    Pin the ranking's stage list to the pipeline it describes.

    `find_exported_item` ranks stored items by how far each got, which is only meaningful
    while this tuple lists the stages in the order `_process_transcript` applies them. The
    check is against the source of that function, so reordering or renaming a stage there
    without touching the tuple fails here rather than silently degrading a re-export into
    picking the wrong item.
    """
    import inspect

    from deep_transcribe.transcribe_commands import PIPELINE_STAGE_ORDER, _process_transcript

    source = inspect.getsource(_process_transcript)
    # The stages that appear as `result = <stage>(...)` in the body, in body order.
    called = re.findall(r"result = (\w+)\(", source)
    known = [name for name in called if name in PIPELINE_STAGE_ORDER]

    assert known, f"no stage in {PIPELINE_STAGE_ORDER} is called in _process_transcript"
    ranks = [PIPELINE_STAGE_ORDER.index(name) for name in known]
    assert ranks == sorted(ranks), (
        f"_process_transcript runs {known}, which is not the order PIPELINE_STAGE_ORDER lists"
    )


def _write_doc(
    docs_dir: Path, name: str, *, last_stage: str, created_at: str, url: str = REPORT_SOURCE_URL
) -> None:
    """A stored doc item with the history and timestamp the ranking reads, and nothing else."""
    import yaml

    docs_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "type": "doc",
        "format": "md_html",
        "url": url,
        "created_at": created_at,
        "history": [{"action_name": "transcribe"}, {"action_name": last_stage}],
    }
    frontmatter = yaml.safe_dump(metadata, sort_keys=True)
    (docs_dir / f"{name}.doc.md").write_text(
        f"---\n{frontmatter}---\n\n## A section\n", encoding="utf-8"
    )


def test_the_re_export_prefers_a_finished_run_over_a_newer_unfinished_one(
    tmp_path: Path,
) -> None:
    """
    The case the measured workspace holds: a run that died after concepts sits beside an
    older run that finished, and the newer one has the newer timestamp and just as many
    history entries. Rebuilding the page from the item that never reached the index loses
    the index, the timeline and the concept map, and the only sign is a thinner page.

    Ranking on how far each run actually got is what separates them, so this is the check
    that a count of history entries cannot pass.
    """
    from deep_transcribe.transcribe_commands import find_exported_item

    class Stub:
        base_dir: Path = tmp_path / "ws"

    docs = Stub.base_dir / "docs"
    _write_doc(
        docs,
        "finished_older",
        last_stage="attach_transcript_index",
        created_at="2026-01-01T00:00:00Z",
    )
    _write_doc(
        docs,
        "unfinished_newer",
        last_stage="extract_transcript_concepts",
        created_at="2026-06-01T00:00:00Z",
    )

    found = find_exported_item(cast("Any", Stub), REPORT_SOURCE_URL)

    assert found is not None
    assert Path(found).name == "finished_older.doc.md", (
        "the re-export took the newer half-finished item over the finished one"
    )


def test_the_re_export_takes_the_newest_of_two_finished_runs(tmp_path: Path) -> None:
    """Two complete runs in one workspace: the page should come from the later result."""
    from deep_transcribe.transcribe_commands import find_exported_item

    class Stub:
        base_dir: Path = tmp_path / "ws"

    docs = Stub.base_dir / "docs"
    _write_doc(
        docs, "first_run", last_stage="attach_transcript_index", created_at="2026-01-01T00:00:00Z"
    )
    _write_doc(
        docs, "second_run", last_stage="attach_transcript_index", created_at="2026-06-01T00:00:00Z"
    )

    found = find_exported_item(cast("Any", Stub), REPORT_SOURCE_URL)

    assert found is not None
    assert Path(found).name == "second_run.doc.md"


def test_the_re_export_ignores_items_from_another_source(tmp_path: Path) -> None:
    """One workspace can hold several recordings; a re-export must not cross between them."""
    from deep_transcribe.transcribe_commands import find_exported_item

    class Stub:
        base_dir: Path = tmp_path / "ws"

    docs = Stub.base_dir / "docs"
    _write_doc(
        docs,
        "another_recording",
        last_stage="attach_transcript_index",
        created_at="2026-06-01T00:00:00Z",
        url="https://example.com/something-else",
    )

    assert find_exported_item(cast("Any", Stub), REPORT_SOURCE_URL) is None


def test_re_exporting_a_workspace_with_no_run_says_so(tmp_path: Path) -> None:
    """
    The mistyped workspace or source. The answer is one line the CLI turns into a usage
    error, not a traceback and not an empty page.
    """
    from deep_transcribe.transcribe_commands import NoCachedResult, export_only

    ws_root = _own_workspace(tmp_path)
    ws_root.mkdir(parents=True)

    with pytest.raises(NoCachedResult) as raised:
        export_only(ws_root, REPORT_SOURCE_URL)

    message = str(raised.value)
    assert REPORT_SOURCE_URL in message
    assert "--export-only" in message
