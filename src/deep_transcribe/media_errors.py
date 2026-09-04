"""
Turn the failures a media run actually hits into one actionable line each.

kash does not wrap yt-dlp's exceptions, so a disk-full download reached the user as a raw
`UnavailableVideoError` traceback ending in `[Errno 28] No space left on device`, followed
by a friendly line nobody was still reading. A two-hour run that ends in a stack dump has
thrown away the one sentence that says what to do next.

Only the recognized failures are rewritten. Anything unrecognized keeps the full report,
because a traceback beats a confident wrong summary.
"""

from __future__ import annotations

import errno
import re
from pathlib import Path
from urllib.parse import urlparse

from deep_transcribe.disk_space import InsufficientDiskSpace, volume_for

_YTDLP_ROUTING_PREFIX = re.compile(r"^\[[a-z][a-z0-9:_.-]*\]\s+(?:[^\s:]+:\s+)?")
_YTDLP_BOILERPLATE = re.compile(r";\s*please report this issue.*", re.IGNORECASE | re.DOTALL)
"""yt-dlp appends a bug-report paragraph to extractor errors. It is not the user's problem."""

_NETWORK_ERRNOS = frozenset(
    {
        errno.EHOSTUNREACH,
        errno.EHOSTDOWN,
        errno.ENETUNREACH,
        errno.ENETDOWN,
        errno.ENETRESET,
    }
)
"""
Network failures Python leaves as a plain `OSError`.

The rest already arrive as a recognizable class — `ECONNREFUSED` becomes
`ConnectionRefusedError`, `ETIMEDOUT` becomes `TimeoutError` — and are matched by type. These
five are not mapped to anything, so "No route to host" would otherwise fall through as an
unexplained `OSError`.
"""


def _chain(error: BaseException) -> list[BaseException]:
    """
    Every exception behind this one, cause and context alike.

    The failure worth naming is often not the outermost: yt-dlp reports "unable to
    download" while the `[Errno 28]` two frames down is the only thing the user can act on.
    """
    seen: list[BaseException] = []
    current: BaseException | None = error
    while current is not None and not any(current is found for found in seen):
        seen.append(current)
        current = current.__cause__ or current.__context__
    return seen


def _first(chain: list[BaseException], types: tuple[type, ...]) -> BaseException | None:
    for candidate in chain:
        if isinstance(candidate, types):
            return candidate
    return None


def _network_error_types() -> tuple[type, ...]:
    """
    The network exceptions this project's fetch paths can raise.

    kash fetches media and pages with httpx and curl_cffi, and the research stages use
    requests, so all three are in scope. Imported defensively: a missing optional dependency
    must not turn a network failure into an error about reporting the error.
    """
    types: list[type] = [ConnectionError, TimeoutError]

    import socket

    types.append(socket.gaierror)

    for module_name, names in (
        ("httpx", ("TransportError",)),
        ("requests.exceptions", ("ConnectionError", "Timeout")),
        ("urllib3.exceptions", ("HTTPError",)),
        ("curl_cffi.requests.exceptions", ("RequestException",)),
    ):
        try:
            module = __import__(module_name, fromlist=list(names))
        except ImportError:  # pragma: no cover - depends on what is installed
            continue
        for name in names:
            found = getattr(module, name, None)
            if isinstance(found, type) and issubclass(found, BaseException):
                types.append(found)
    return tuple(types)


def _ytdlp_error_types() -> tuple[type, ...]:
    """
    `DownloadError`, `ExtractorError`, and `UnavailableVideoError`, via their common base.

    All three derive from `YoutubeDLError`, and matching the base also covers the
    geo-restriction and sign-in errors yt-dlp raises under other names.
    """
    from yt_dlp.utils import YoutubeDLError

    return (YoutubeDLError,)


def _one_line_reason(error: BaseException, *, strip_routing: bool = False) -> str:
    """
    yt-dlp's own explanation, trimmed to the part that says what went wrong.

    `orig_msg` is the extractor's sentence before yt-dlp decorates it; `str()` on a
    `DownloadError` carries the `ERROR:` prefix its console printer adds.
    """
    raw = getattr(error, "orig_msg", None)
    if not isinstance(raw, str) or not raw.strip():
        raw = str(error)
    reason = _YTDLP_BOILERPLATE.sub("", raw).strip()
    reason = reason.splitlines()[0].strip() if reason else ""
    for prefix in ("ERROR: ", "Unable to download video: "):
        if reason.startswith(prefix):
            reason = reason[len(prefix) :].strip()
    # yt-dlp prefixes its reason with `[extractor] id:` — routing, not diagnosis, and the
    # URL in our message already names the video. Left in, it is also mangled on the way
    # out: kash renders the console through Rich, which reads `[youtube]` as a markup tag
    # and drops it, so the user saw `:  zzzzzzzzzzz: This video is unavailable` with a
    # double space and no hint of what the bare id was doing there.
    if strip_routing:
        reason = _YTDLP_ROUTING_PREFIX.sub("", reason, count=1)
    return reason.rstrip(".").strip() or "the download failed"


def _host_of(error: BaseException, source: str | None) -> str | None:
    """The host the failed request was aimed at, from the exception or from the source URL."""
    request = getattr(error, "request", None)
    url = getattr(request, "url", None)
    host = getattr(url, "host", None)
    if isinstance(host, str) and host:
        return host
    if isinstance(url, str) and url:
        parsed = urlparse(url)
        if parsed.hostname:
            return parsed.hostname
    if source:
        parsed = urlparse(source)
        if parsed.hostname:
            return parsed.hostname
    return None


def _volume_of(error: BaseException, workspace_path: Path | None) -> Path | None:
    """The volume that filled up, named from the file being written or from the workspace."""
    filename = getattr(error, "filename", None)
    for candidate in (filename, workspace_path):
        if candidate:
            return volume_for(Path(candidate))
    return None


def explain_error(
    error: BaseException,
    *,
    source: str | None = None,
    workspace_path: Path | None = None,
) -> str | None:
    """
    One actionable line for a recognized failure, or None to keep the full report.

    Ordered by what the user can act on rather than by what wrapped what. A download that
    filled the disk raises a yt-dlp error with the `ENOSPC` underneath, and "free some
    space" is the useful half of that pair.
    """
    chain = _chain(error)

    stop = _first(chain, (InsufficientDiskSpace,))
    if stop is not None:
        return str(stop)

    full = next(
        (
            candidate
            for candidate in chain
            if isinstance(candidate, OSError) and candidate.errno == errno.ENOSPC
        ),
        None,
    )
    if full is not None:
        volume = _volume_of(full, workspace_path)
        where = f" on {volume}" if volume else ""
        return (
            f"Ran out of space{where} while downloading this source. "
            f"Free space or use --workspace on another volume."
        )

    download = _first(chain, _ytdlp_error_types())
    if download is not None:
        what = source or "this source"
        return (
            f"Could not download {what}: {_one_line_reason(download, strip_routing=True)}. "
            f"Check the URL, your network, or whether the video is private/geo-blocked."
        )

    network = _first(chain, _network_error_types()) or next(
        (
            candidate
            for candidate in chain
            if isinstance(candidate, OSError) and candidate.errno in _NETWORK_ERRNOS
        ),
        None,
    )
    if network is not None:
        host = _host_of(network, source)
        where = host or "the source"
        return (
            f"Could not reach {where}: {_one_line_reason(network)}. "
            f"Check your network connection and try again."
        )

    return None


## Tests


def test_a_disk_full_download_reads_as_disk_full_not_as_a_video_problem(tmp_path: Path) -> None:
    """
    The failure that prompted this: yt-dlp reported an unavailable video, and the real
    cause was `[Errno 28]` two frames down. Reporting the outer exception would send the
    user to check whether the video is private while their disk stays full.
    """
    from yt_dlp.utils import UnavailableVideoError

    full = OSError(errno.ENOSPC, "No space left on device", str(tmp_path / "video.mp4.part"))
    try:
        try:
            raise full
        except OSError as cause:
            raise UnavailableVideoError("boom") from cause
    except UnavailableVideoError as error:
        explained = explain_error(error, source="https://youtube.com/watch?v=abc")

    assert explained is not None
    assert explained.startswith(f"Ran out of space on {volume_for(tmp_path)} while downloading")
    assert "--workspace on another volume" in explained
    assert "private" not in explained, f"blamed the video for a full disk: {explained}"


def test_a_download_error_carries_yt_dlps_own_reason() -> None:
    """
    The extractor tag stays. `[youtube] abc:` is yt-dlp's own wording, and trimming it back
    to a bare sentence would start editing diagnoses this code is not qualified to edit —
    only the `ERROR:` prefix its console printer adds comes off.
    """
    from yt_dlp.utils import DownloadError

    explained = explain_error(
        DownloadError("ERROR: [youtube] abc: Video unavailable"),
        source="https://youtube.com/watch?v=abc",
    )

    assert explained == (
        "Could not download https://youtube.com/watch?v=abc: Video unavailable. "
        "Check the URL, your network, or whether the video is private/geo-blocked."
    )


def test_an_extractor_error_drops_yt_dlps_bug_report_paragraph() -> None:
    """
    yt-dlp appends "please report this issue on github…" to extractor errors. A private
    video is not a yt-dlp bug, and the paragraph is longer than the reason it follows.
    """
    from yt_dlp.utils import ExtractorError

    explained = explain_error(
        ExtractorError("Private video. Sign in if you have been granted access", video_id="abc"),
        source="https://youtube.com/watch?v=abc",
    )

    assert explained is not None
    assert "Private video. Sign in if you have been granted access." in explained
    assert "github.com/yt-dlp" not in explained, explained
    assert "yt-dlp -U" not in explained, explained


def test_a_network_failure_names_the_host() -> None:
    import httpx

    request = httpx.Request("GET", "https://rr3---sn-x.googlevideo.com/videoplayback?id=1")
    explained = explain_error(
        httpx.ConnectError("[Errno 8] nodename nor servname provided", request=request)
    )

    assert explained == (
        "Could not reach rr3---sn-x.googlevideo.com: "
        "[Errno 8] nodename nor servname provided. "
        "Check your network connection and try again."
    )


def test_a_network_failure_without_a_request_falls_back_to_the_source_host() -> None:
    explained = explain_error(
        TimeoutError("timed out"), source="https://podcasts.apple.com/us/podcast/x"
    )

    assert explained is not None
    assert "Could not reach podcasts.apple.com: timed out." in explained


def test_no_route_to_host_is_recognized_though_python_leaves_it_a_bare_oserror() -> None:
    """
    `EHOSTUNREACH` and `ENETUNREACH` get no dedicated exception class, so matching on type
    alone would let the most ordinary "your wifi is down" failure through unexplained.
    """
    unreachable = OSError(errno.EHOSTUNREACH, "No route to host")

    explained = explain_error(unreachable, source="https://youtube.com/watch?v=abc")

    assert explained is not None
    assert "Could not reach youtube.com:" in explained
    assert "No route to host." in explained
    assert "Check your network connection" in explained


def test_the_preflight_stop_passes_through_unchanged() -> None:
    """It is already the finished sentence, and rewrapping it would only dilute it."""
    stop = InsufficientDiskSpace("Not enough free space on /Volumes/Backup to download this.")

    assert explain_error(stop) == "Not enough free space on /Volumes/Backup to download this."


def test_an_unrecognized_failure_keeps_the_full_report() -> None:
    """
    A confident wrong summary is worse than a traceback. Anything not mapped here stays
    exactly as loud as it was.
    """
    assert explain_error(ValueError("something structural went wrong")) is None
    assert explain_error(KeyError("speaker_roster")) is None


def test_a_non_network_oserror_is_not_mistaken_for_one() -> None:
    """
    `OSError` covers far more than the network, and a missing file reported as a connection
    problem sends the user to restart their router.
    """
    assert explain_error(FileNotFoundError(errno.ENOENT, "No such file", "/tmp/nope")) is None


def test_the_real_message_for_a_bad_video_id_reads_cleanly() -> None:
    """
    Captured from the binary on `watch?v=zzzzzzzzzzz`. yt-dlp's `[youtube] id:` prefix is
    routing, and Rich eats the bracketed part as markup, so keeping it produced
    `:  zzzzzzzzzzz: This video is unavailable` on the console.
    """
    from yt_dlp.utils import DownloadError

    message = explain_error(
        DownloadError("ERROR: [youtube] zzzzzzzzzzz: This video is unavailable"),
        source="https://www.youtube.com/watch?v=zzzzzzzzzzz",
        workspace_path=None,
    )
    assert message is not None
    assert message.startswith(
        "Could not download https://www.youtube.com/watch?v=zzzzzzzzzzz: This video is unavailable. "
    )
    assert "[" not in message.split(". ")[0] and "  " not in message


def test_a_tag_with_no_video_id_is_stripped_too() -> None:
    from yt_dlp.utils import DownloadError

    message = explain_error(
        DownloadError("ERROR: [generic] Unsupported URL"),
        source="https://x.test/a",
        workspace_path=None,
    )
    assert message is not None and ": Unsupported URL. " in message
