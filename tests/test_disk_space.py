# pyright: reportPrivateUsage=false

"""
The disk-space preflights, driven through the real pipeline entry points.

A run on a five-hour source takes about two hours, and the failure these checks exist to
prevent showed up twenty minutes in, after the download had already filled the volume. So
what has to be proven here is not that the arithmetic is right — that is checked beside the
arithmetic — but that the check runs on the right volume, before the fetch, and stops.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

import pytest

if TYPE_CHECKING:
    from kash.model import Item

from deep_transcribe import transcribe_commands
from deep_transcribe.disk_space import InsufficientDiskSpace, _mount_point
from deep_transcribe.transcribe_options import TranscribeOptions

MEASURED_SECONDS = 18900
"""5h15m, the length the message shape in the bead was written against."""

GB = 1000**3
MB = 1000**2


class _Usage(NamedTuple):
    total: int
    used: int
    free: int


def _fake_disk_usage(monkeypatch: pytest.MonkeyPatch, free: int, asked: list[Path]) -> None:
    """
    Report a fixed amount free, recording every path the code asked about.

    The recording is the point. A check that consulted `/` instead of the workspace would
    raise the same message on a machine whose boot volume happens to be full and stay
    silent on every machine where it is not, and no assertion about the message text can
    tell those two apart.
    """

    def fake(path: str | Path) -> _Usage:
        asked.append(Path(path))
        return _Usage(total=free * 4, used=free * 3, free=free)

    monkeypatch.setattr(shutil, "disk_usage", fake)


def _own_workspace(tmp_path: Path) -> Path:
    """
    A workspace root whose name no other test shares.

    kash's registry is keyed by directory name, so two tests sharing one resolve
    `current_ws()` to whichever registered first. Same reasoning as the helper of the same
    name in `test_transcribe_commands.py`.
    """
    return tmp_path / f"ws-{tmp_path.name}"


def _source_item(duration: int | None) -> Item:
    """
    The resource as kash stores it after the metadata fetch.

    `duration` is present and None for a local file or a URL no media service claims, which
    is why the key is always written.
    """
    from kash.model import Format, Item, ItemType
    from kash.utils.common.url import Url

    return Item(
        type=ItemType.resource,
        format=Format.url,
        url=Url("https://example.com/video"),
        title="A long interview",
        extra={"duration": duration},
    )


def _drive_run_transcription(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    free: int,
    asked: list[Path],
    reached: list[str],
    duration: int | None = MEASURED_SECONDS,
) -> Path:
    """
    Run the real `run_transcription` with only the fetch and the output faked.

    `_prepare_source_item` stands in for the metadata fetch, which in the real path is a
    `download=False` call to yt-dlp — so the item it returns carries the duration exactly
    where kash puts it, and nothing large has been written yet. Whether `reached` fills in
    is the whole question: reaching transcription means the download would have started.

    Returns the workspace root, and reports through the caller's lists so they can still be
    read after the preflight raises.
    """

    def fake_prepare(_source: str) -> Item:
        return _source_item(duration)

    def fake_transcribe(item: Item, *_args: object, **_kwargs: object) -> Item:
        reached.append("transcribe")
        return item

    def fake_format(_result: Item, _base_dir: Path, **_kwargs: object) -> tuple[Path, Path]:
        return Path("transcript.md"), Path("transcript.html")

    monkeypatch.setattr(transcribe_commands, "_prepare_source_item", fake_prepare)
    monkeypatch.setattr(transcribe_commands, "transcribe_with_options", fake_transcribe)
    monkeypatch.setattr(transcribe_commands, "format_results", fake_format)

    ws_root = _own_workspace(tmp_path)
    ws_root.mkdir(parents=True, exist_ok=True)
    _fake_disk_usage(monkeypatch, free, asked)

    transcribe_commands.run_transcription(
        ws_root,
        "https://example.com/video",
        TranscribeOptions.basic(),
        "en",
    )
    return ws_root


def test_a_full_volume_stops_before_the_download_starts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    The run that prompted this died twenty minutes into a download, having spent the time
    and filled the volume. With 1.1 GB free and a 5h15m source needing about 4.2, the
    answer was knowable before the first byte, so nothing may be fetched.
    """
    asked: list[Path] = []
    reached: list[str] = []
    ws_root = _own_workspace(tmp_path)

    with pytest.raises(InsufficientDiskSpace) as raised:
        _drive_run_transcription(
            tmp_path, monkeypatch, free=int(1.1 * GB), asked=asked, reached=reached
        )

    reported = str(raised.value)
    assert reached == [], "the download started anyway"
    assert f"Not enough free space on {_mount_point(ws_root)} " in reported, reported
    assert "about 4.2 GB needed for a 5h15m recording" in reported, reported
    assert "1.1 GB free" in reported, reported
    assert "--workspace on another volume" in reported, reported


def test_the_check_reads_the_workspace_volume_and_not_the_boot_volume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    `--workspace` on a roomier disk is the escape hatch the message offers, and the advice
    is only true if the check looked where the media will actually land.
    """
    asked: list[Path] = []
    reached: list[str] = []
    ws_root = _own_workspace(tmp_path)

    with pytest.raises(InsufficientDiskSpace):
        _drive_run_transcription(
            tmp_path, monkeypatch, free=int(1.1 * GB), asked=asked, reached=reached
        )

    assert asked, "the preflight never called shutil.disk_usage at all"
    assert all(str(path).startswith(str(ws_root)) for path in asked), (
        f"consulted something other than the workspace volume: {asked}"
    )


def test_a_volume_with_room_lets_the_run_proceed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    The check is a stop, not a warning, so the case that matters just as much is that a
    machine with space is untouched by it.
    """
    asked: list[Path] = []
    reached: list[str] = []

    _drive_run_transcription(tmp_path, monkeypatch, free=500 * GB, asked=asked, reached=reached)

    assert asked, "the preflight never ran at all, so the passing case proves nothing"
    assert reached == ["transcribe"], "a run with 500 GB free did not reach transcription"


def test_an_unknown_duration_still_gets_the_floor_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    A local file, or a URL no media service claims, reports no duration. That is a reason
    to check less, not a reason to check nothing: under a gigabyte free fails regardless,
    and the message must not invent a length it does not know.
    """
    asked: list[Path] = []
    reached: list[str] = []

    with pytest.raises(InsufficientDiskSpace) as raised:
        _drive_run_transcription(
            tmp_path,
            monkeypatch,
            free=200 * MB,
            asked=asked,
            reached=reached,
            duration=None,
        )

    reported = str(raised.value)
    assert reached == []
    assert "about 1.0 GB needed, 200 MB free" in reported, reported
    assert "recording" not in reported, f"claimed a length it does not know: {reported}"


def test_frame_capture_stops_before_writing_the_first_jpg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Frame capture runs after the LLM stages, so a run that dies here has already paid for
    everything above it. Driven through `_process_transcript` because that is where the
    stage is reached, and in its own workspace because the check reads `current_ws()`.
    """
    from kash.exec import kash_runtime
    from kash.kits.media.actions.transcribe import insert_frame_captures as frame_module
    from kash.model import Format, Item, ItemType
    from kash.workspaces import current_ws

    def unreachable(*_args: object, **_kwargs: object) -> Item:
        raise AssertionError("frame capture ran on a volume with no room for it")

    monkeypatch.setattr(frame_module, "insert_frame_captures", unreachable)

    workspace_path = _own_workspace(tmp_path)
    item = Item(
        type=ItemType.doc,
        format=Format.md_html,
        title="A recording",
        body="A paragraph. <span data-timestamp='4.56' />\n",
    )

    asked: list[Path] = []
    with kash_runtime(workspace_path):
        base_dir = current_ws().base_dir
        assert base_dir.resolve() == workspace_path.resolve(), (
            f"the runtime used workspace {base_dir}, not {workspace_path}"
        )
        _fake_disk_usage(monkeypatch, 200 * MB, asked)
        with pytest.raises(InsufficientDiskSpace) as raised:
            transcribe_commands._process_transcript(
                item,
                TranscribeOptions(insert_frame_captures=True),
                processing_instructions=None,
            )

    reported = str(raised.value)
    assert (
        f"Not enough free space on {_mount_point(workspace_path)} for frame capture" in reported
    ), reported
    assert "about 500 MB needed, 200 MB free" in reported, reported
    assert asked and all(str(path).startswith(str(workspace_path)) for path in asked), (
        f"frame capture checked the wrong volume: {asked}"
    )
