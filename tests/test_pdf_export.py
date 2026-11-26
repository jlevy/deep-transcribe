from pathlib import Path

import pytest

from deep_transcribe import pdf_export


def test_pdf_export_does_not_replace_existing_file_on_partial_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "out.pdf"
    destination.write_bytes(b"previous PDF")

    def broken_print(_browser: str, _html: Path, staged_pdf: Path) -> None:
        staged_pdf.write_bytes(b"%PDF-1.7\npartial")
        assert not pdf_export._complete_pdf(staged_pdf)  # pyright: ignore[reportPrivateUsage]
        raise pdf_export.PdfExportError("browser timed out")

    monkeypatch.setattr(pdf_export, "_print_pdf", broken_print)
    with pytest.raises(pdf_export.PdfExportError, match="browser timed out"):
        pdf_export.export_pdf("chrome", tmp_path / "transcript.html", destination)

    assert destination.read_bytes() == b"previous PDF"
    assert list(tmp_path.iterdir()) == [destination]
