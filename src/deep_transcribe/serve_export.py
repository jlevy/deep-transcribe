"""
Serve a finished export over loopback HTTP and open it in the browser.

An export opened straight from disk reaches the browser as a `file://` URL, and YouTube
refuses to embed its player for a page that sends no referer: the embed fails with player
error 153. The page's own fallback then opens YouTube in a new tab, so a click on a
timeline block or a timestamp leaves the transcript instead of opening the popover the
page is built around. Serving the same file over `http://127.0.0.1` gives the page a real
origin and the embedded player works, at the cost of a process that stays in the
foreground while the user reads.
"""

import logging
import socket
import threading
import webbrowser
from dataclasses import dataclass
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, override
from urllib.parse import quote

log = logging.getLogger(__name__)

LOOPBACK_HOST = "127.0.0.1"
"""
The only address this ever binds.

A transcript is private, and this is a convenience for the person at the keyboard rather
than a web server, so the socket must not be reachable from the network.
"""


class _QuietHandler(SimpleHTTPRequestHandler):
    """`SimpleHTTPRequestHandler` without a line of stderr per request."""

    @override
    def log_message(self, format: str, *args: Any) -> None:
        # One page pulls hundreds of frame captures, and a line each would scroll the URL
        # the user is meant to read off the screen. The log file still gets them.
        log.debug("%s - %s", self.address_string(), format % args)


@dataclass(frozen=True)
class ExportServer:
    """
    A running loopback server for one export, and the URL that reaches it.

    `host` and `port` are read back from the bound socket rather than from what was asked
    for, so they describe what the kernel actually did.
    """

    url: str
    host: str
    port: int
    directory: Path
    _server: ThreadingHTTPServer
    _thread: threading.Thread

    def shutdown(self) -> None:
        """Stop serving and release the port."""
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)

    def block_until_interrupt(self) -> None:
        """
        Serve until the user interrupts, then stop.

        `KeyboardInterrupt` is re-raised so the CLI's own handler reports the interrupt in
        the usual way. Joining with a timeout rather than waiting outright is what lets
        the signal reach this thread at all.
        """
        try:
            while self._thread.is_alive():
                self._thread.join(timeout=0.2)
        except KeyboardInterrupt:
            self.shutdown()
            raise


def serve_export(export_path: Path) -> ExportServer:
    """
    Start serving the directory `export_path` sits in, on an OS-assigned free port.

    The directory, not the single file: the page's images live in a sibling `.assets`
    directory and have to be reachable under the same origin.
    """
    export_path = export_path.resolve()
    directory = export_path.parent
    handler = partial(_QuietHandler, directory=str(directory))
    server = ThreadingHTTPServer((LOOPBACK_HOST, 0), handler)
    host, port = server.socket.getsockname()[:2]
    thread = threading.Thread(
        target=server.serve_forever,
        name="deep-transcribe-export-server",
        daemon=True,
    )
    thread.start()
    log.info("Serving %s on %s:%s", directory, host, port)
    return ExportServer(
        url=f"http://{host}:{int(port)}/{quote(export_path.name)}",
        host=str(host),
        port=int(port),
        directory=directory,
        _server=server,
        _thread=thread,
    )


def serve_and_open(
    export_path: Path,
    *,
    open_browser: bool = True,
    block: bool = True,
) -> ExportServer:
    """
    Serve one export, open it in the default browser, and keep serving.

    The URL is `ExportServer.url`. Pass `open_browser=False` to leave the browser alone
    and `block=False` to get the server back immediately, which is also what a caller
    that has to print the URL before it stops for the user needs.
    """
    served = serve_export(export_path)
    if open_browser:
        webbrowser.open(served.url)
    if block:
        served.block_until_interrupt()
    return served


## Tests


def test_serve_export_serves_the_page_and_its_assets_over_loopback(tmp_path: Path) -> None:
    """
    The two things the flag exists for: the page comes back, and so do the images beside
    it, both from an address that only this machine can reach.
    """
    import urllib.request

    import pytest

    exports = tmp_path / "exports"
    assets = exports / "recording.assets"
    assets.mkdir(parents=True)
    page = exports / "recording.html"
    page_bytes = b"<html><body><img src='recording.assets/frame_0000.jpg'></body></html>"
    page.write_bytes(page_bytes)
    frame_bytes = b"\xff\xd8\xff\xe0 not really a jpeg"
    (assets / "frame_0000.jpg").write_bytes(frame_bytes)

    served = serve_and_open(page, open_browser=False, block=False)
    try:
        assert served.url == f"http://127.0.0.1:{served.port}/recording.html"

        with urllib.request.urlopen(served.url, timeout=10) as response:
            assert response.status == 200
            assert response.read() == page_bytes

        asset_url = f"http://127.0.0.1:{served.port}/recording.assets/frame_0000.jpg"
        with urllib.request.urlopen(asset_url, timeout=10) as response:
            assert response.status == 200
            assert response.read() == frame_bytes

        # Read back from the socket, so this is the bind the kernel made and not the
        # constant above: a wildcard bind would report 0.0.0.0 here.
        assert served.host == LOOPBACK_HOST

        # And nothing on this host's own routable addresses answers on that port.
        routable = {
            str(info[4][0])
            for info in socket.getaddrinfo(
                socket.gethostname(), served.port, socket.AF_INET, socket.SOCK_STREAM
            )
        } - {LOOPBACK_HOST}
        for address in sorted(routable):
            with pytest.raises(OSError):
                socket.create_connection((address, served.port), timeout=2).close()
    finally:
        served.shutdown()

    # The port is free again, which is the observable half of a clean shutdown.
    with pytest.raises(OSError):
        socket.create_connection((LOOPBACK_HOST, served.port), timeout=2).close()
