# pyright: reportPrivateUsage=false

import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

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
