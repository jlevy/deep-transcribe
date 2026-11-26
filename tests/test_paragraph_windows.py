import re

import pytest
from flexdoc import FlexDoc

from deep_transcribe import paragraph_windows
from deep_transcribe.paragraph_windows import repair_paragraph_body


def test_paragraph_repair_preserves_source_repetition_markup_and_paragraphs() -> None:
    source = (
        "**Ada:** It’s ready. Say it again. Say it again. The first topic ends here. "
        "**Grace:** A new topic starts now. The final sentence stays intact."
    )
    formatted = (
        "**Ada:** It’s ready.\n\nSay it again. Say it again. The first topic ends here.\n\n"
        "<!--window-br-->Say it again. The first topic ends here.\n\n"
        "**Grace:** A new topic starts now. The final sentence stays intact."
    )

    repaired = repair_paragraph_body(source, formatted)

    assert re.sub(r"\s+", "", repaired) == re.sub(r"\s+", "", source)
    assert repaired.count("Say it again.") == 2
    assert "\n\nSay it again." in repaired
    assert "<!--window-br-->" not in repaired
    assert repair_paragraph_body(source, source) == source


def test_paragraph_repair_restores_missing_source_and_rejects_unmatched_model_edits() -> None:
    source = "**Ada:** Keep this opening. Preserve every source word. Repeat. Repeat."
    formatted = "**Ada:** Keep this opening.\n\n<!--window-br-->Invented model words. Repeat."

    repaired = repair_paragraph_body(source, formatted)

    assert re.sub(r"\s+", "", repaired) == re.sub(r"\s+", "", source)
    assert "Invented model words" not in repaired
    assert repaired.count("Repeat.") == 2


def test_paragraph_repair_falls_back_to_complete_source_on_invariant_failure(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    source = "**Ada:** Every spoken word must survive.\n\nKeep this paragraph too."

    def broken_filter(*_args: object) -> FlexDoc:
        return FlexDoc.from_text("The filter unexpectedly lost source text.")

    monkeypatch.setattr(paragraph_windows, "filtered_transform", broken_filter)

    assert repair_paragraph_body(source, "Changed words.") == source
    assert "using the complete source with its original paragraph breaks" in caplog.text
