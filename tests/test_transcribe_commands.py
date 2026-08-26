# pyright: reportPrivateUsage=false

from pathlib import Path
from tempfile import TemporaryDirectory

from deep_transcribe.transcribe_commands import _media_source_locator


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
