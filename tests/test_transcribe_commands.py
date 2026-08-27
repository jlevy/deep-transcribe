# pyright: reportPrivateUsage=false

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

    result = unwrap(transcribe_commands._attach_processing_instructions)(
        item,
        processing_instructions=instructions,
    )

    assert result is not item
    assert result.store_path is None
    assert get_processing_instructions(item) is None
    assert get_processing_instructions(result) == instructions
