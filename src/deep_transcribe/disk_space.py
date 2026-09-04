"""
Refuse to start work that will not fit on the disk it is about to be written to.

A long run is expensive in wall-clock time, so the failures worth catching are the ones
that are certain before any of that time is spent. Running out of space mid-download is
one of them: the source duration is known from the service metadata before a single byte
of media is fetched, and free space is a syscall away, so the two can be compared while
the run has cost nothing.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kash.model import Item

GB = 1000**3
MB = 1000**2

BYTES_PER_HOUR = 800 * MB
"""
Conservative bytes of media cache per hour of source.

Measured on a 5.26-hour interview: 4.0 GB of media cache, holding full-quality audio, the
16 kHz mp3 sent to speech-to-text, and the original m4a. That is 760 MB/hour; the figure
here rounds up so the estimate errs toward stopping a run that would have just fit rather
than starting one that will not.
"""

DOWNLOAD_FLOOR = 1 * GB
"""
Least free space worth starting any download with, however short the source.

Short sources still pull a container, a conversion, and the workspace around them, and a
volume with less than this free is about to cause trouble in some other stage anyway.
Also the whole estimate when the duration is unknown, which is the case for a plain URL
no media service recognizes.
"""

FRAME_CAPTURE_FLOOR = 500 * MB
"""
Least free space worth starting frame capture with.

Frames for the same 5.26-hour recording were 115 MB of jpgs before thinning. The stage is
bounded enough that a flat figure with room to spare beats an estimate.
"""


class InsufficientDiskSpace(Exception):
    """
    A stage would not fit on the volume it writes to.

    Carries the finished user-facing sentence, because there is nothing the caller can add
    that the check did not already know.
    """


def _mount_point(path: Path) -> Path:
    """The volume `path` lives on, named the way the user's disk tools name it."""
    current = path
    while not os.path.ismount(current) and current != current.parent:
        current = current.parent
    return current


def _nearest_existing(path: Path) -> Path:
    """
    Walk up to something that exists, since a workspace is often created by the run.

    `shutil.disk_usage` raises on a path that is not there yet, and the answer for the
    parent directory is the answer for the volume either way.
    """
    current = path
    while not current.exists() and current != current.parent:
        current = current.parent
    return current


def free_bytes(path: Path) -> int:
    """Free space on the volume holding `path`, whether or not `path` exists yet."""
    return shutil.disk_usage(_nearest_existing(path)).free


def fmt_size(size: int) -> str:
    """Sizes as disk tools report them, so a comparison with the volume's own numbers holds."""
    if size >= GB:
        return f"{size / GB:.1f} GB"
    return f"{round(size / MB)} MB"


def fmt_duration(seconds: float) -> str:
    """A recording length a person recognizes: `5h15m`, `47m`, `38s`."""
    total = int(round(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h{minutes:02d}m"
    if minutes:
        return f"{minutes}m"
    return f"{secs}s"


def estimate_download_bytes(duration_seconds: float | None) -> int:
    """
    Space the media cache will need for a source of this length.

    An unknown duration falls back to the floor rather than to no check at all: a volume
    with under a gigabyte free fails on any source, and that much is knowable.
    """
    if duration_seconds is None or duration_seconds <= 0:
        return DOWNLOAD_FLOOR
    return max(DOWNLOAD_FLOOR, int(duration_seconds / 3600 * BYTES_PER_HOUR))


def source_duration(item: Item) -> float | None:
    """
    Source length in seconds from the fetched resource, or None when nothing reported one.

    yt-dlp reports the duration in the service metadata, which kash stores in the item's
    `extra` before any media is downloaded — which is what makes a sized check possible
    while the run has still cost nothing. A local file, or a URL no media service claims,
    leaves the key present and None.
    """
    duration = (item.extra or {}).get("duration")
    if isinstance(duration, bool) or not isinstance(duration, (int, float)):
        return None
    return float(duration) if duration > 0 else None


def _report(
    workspace_path: Path, what: str, needed: int, available: int, qualifier: str = ""
) -> str:
    volume = _mount_point(_nearest_existing(workspace_path))
    return (
        f"Not enough free space on {volume} {what}: "
        f"about {fmt_size(needed)} needed{qualifier}, {fmt_size(available)} free. "
        f"Free space or use --workspace on another volume."
    )


def check_download_space(workspace_path: Path, duration_seconds: float | None = None) -> None:
    """
    Stop before fetching media that will not fit under the workspace directory.

    Both the kash workspace and the media cache sit under the `--workspace` directory, so
    the volume that matters is the one it is on, not the boot volume — which is the whole
    point of being able to point `--workspace` somewhere else.
    """
    needed = estimate_download_bytes(duration_seconds)
    available = free_bytes(workspace_path)
    if available >= needed:
        return
    length = f" for a {fmt_duration(duration_seconds)} recording" if duration_seconds else ""
    raise InsufficientDiskSpace(
        _report(workspace_path, "to download this source", needed, available, length)
    )


def check_frame_capture_space(workspace_path: Path) -> None:
    """Stop before frame capture rather than partway through writing jpgs."""
    available = free_bytes(workspace_path)
    if available >= FRAME_CAPTURE_FLOOR:
        return
    raise InsufficientDiskSpace(
        _report(workspace_path, "for frame capture", FRAME_CAPTURE_FLOOR, available)
    )


## Tests


def test_the_estimate_matches_the_measured_recording() -> None:
    """
    The 5.26-hour interview filled 4.0 GB of media cache. An estimate that came in under
    that would have let the run that prompted this check start anyway.
    """
    measured_seconds = 5.26 * 3600
    measured_cache = int(4.0 * GB)

    assert estimate_download_bytes(measured_seconds) > measured_cache
    assert fmt_size(estimate_download_bytes(measured_seconds)) == "4.2 GB"


def test_short_and_unknown_sources_fall_back_to_the_floor() -> None:
    assert estimate_download_bytes(60) == DOWNLOAD_FLOOR
    assert estimate_download_bytes(None) == DOWNLOAD_FLOOR
    assert estimate_download_bytes(0) == DOWNLOAD_FLOOR


def test_durations_read_the_way_a_person_says_them() -> None:
    assert fmt_duration(5.25 * 3600) == "5h15m"
    assert fmt_duration(47 * 60) == "47m"
    assert fmt_duration(38) == "38s"


def test_source_duration_reads_the_metadata_yt_dlp_provides() -> None:
    from kash.model import Format, Item, ItemType

    item = Item(type=ItemType.resource, format=Format.url, extra={"duration": 18936})

    assert source_duration(item) == 18936.0
    assert source_duration(Item(type=ItemType.resource, format=Format.url)) is None
    assert (
        source_duration(Item(type=ItemType.resource, format=Format.url, extra={"duration": None}))
        is None
    )


def test_free_bytes_answers_for_a_workspace_that_does_not_exist_yet(tmp_path: Path) -> None:
    """The first run creates the workspace, so the check has to precede the directory."""
    assert free_bytes(tmp_path / "not-created-yet" / "deeper") > 0


def test_the_message_names_the_volume_the_sizes_and_the_way_out(tmp_path: Path) -> None:
    """
    The whole value of the check is in the sentence, so the sentence is worth pinning.

    A message that named the workspace subdirectory rather than the volume would send
    someone to free space in the wrong place, and one that omitted `--workspace` would
    leave the fix undiscoverable.
    """
    reported = _report(
        tmp_path,
        "to download this source",
        int(4.2 * GB),
        1_100_000_000,
        " for a 5h15m recording",
    )

    assert reported == (
        f"Not enough free space on {_mount_point(tmp_path)} to download this source: "
        "about 4.2 GB needed for a 5h15m recording, 1.1 GB free. "
        "Free space or use --workspace on another volume."
    )
