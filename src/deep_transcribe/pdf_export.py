"""Print the existing transcript HTML with Chromium's print layout engine."""

import os
import shutil
import subprocess
import time
from pathlib import Path
from tempfile import TemporaryDirectory, TemporaryFile

from strif import atomic_output_file

_BROWSER_NAMES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome")
_MAC_BROWSERS = (
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
)
_PRINT_TIMEOUT_SECONDS = 180


class PdfExportError(Exception):
    """The browser could not produce a complete PDF."""


def find_pdf_browser() -> str:
    """Find an installed Chrome or Chromium executable."""
    for name in _BROWSER_NAMES:
        if executable := shutil.which(name):
            return executable
    for path in _MAC_BROWSERS:
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
    raise PdfExportError(
        "PDF export requires Google Chrome or Chromium on PATH or in Applications."
    )


def _complete_pdf(path: Path) -> bool:
    try:
        with path.open("rb") as stream:
            if stream.read(5) != b"%PDF-":
                return False
            size = stream.seek(0, os.SEEK_END)
            stream.seek(max(5, size - 128))
            return stream.read().rstrip().endswith(b"%%EOF")
    except FileNotFoundError:
        return False


def _print_pdf(browser: str, html: Path, staged_pdf: Path) -> None:
    with TemporaryDirectory(prefix="deep-transcribe-chrome-") as profile, TemporaryFile() as log:
        command = [
            browser,
            "--headless=new",
            "--disable-background-networking",
            "--no-first-run",
            "--no-default-browser-check",
            "--no-pdf-header-footer",
            "--timeout=30000",
            f"--user-data-dir={profile}",
            f"--print-to-pdf={staged_pdf}",
            html.resolve().as_uri(),
        ]
        with subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT) as process:
            deadline = time.monotonic() + _PRINT_TIMEOUT_SECONDS
            try:
                # Chrome can keep running after writing the PDF. Its trailer confirms
                # that the file is complete even if the isolated browser has not quit.
                while not _complete_pdf(staged_pdf):
                    if (status := process.poll()) is not None:
                        if _complete_pdf(staged_pdf):
                            return
                        log_size = log.seek(0, os.SEEK_END)
                        log.seek(max(0, log_size - 1200))
                        detail = log.read().decode(errors="replace").strip()
                        raise PdfExportError(
                            f"Chrome did not finish the PDF (exit {status}). {detail}"
                        )
                    if time.monotonic() >= deadline:
                        raise PdfExportError("Chrome timed out while printing the transcript PDF.")
                    time.sleep(0.2)
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()


def export_pdf(browser: str, html: Path, destination: Path) -> Path:
    """Apply the HTML print CSS and publish only a complete PDF at the destination."""
    destination = destination.expanduser().absolute()
    with atomic_output_file(destination, make_parents=True, tmp_suffix=".pdf") as staged_pdf:
        try:
            _print_pdf(browser, html, staged_pdf)
        except BaseException:
            staged_pdf.unlink(missing_ok=True)
            raise
    return destination
