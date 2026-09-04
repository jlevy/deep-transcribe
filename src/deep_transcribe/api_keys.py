from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from deep_transcribe.model_profiles import ModelProvider, get_model_profile
from deep_transcribe.transcribe_options import TranscribeOptions

DOCS_URL = "https://github.com/jlevy/deep-transcribe/blob/main/docs/installation.md"

_LLM_KEY_BY_PROVIDER = {
    ModelProvider.anthropic: ("ANTHROPIC_API_KEY", "https://console.anthropic.com/settings/keys"),
    ModelProvider.openai: ("OPENAI_API_KEY", "https://platform.openai.com/api-keys"),
}


@dataclass(frozen=True)
class MissingKey:
    """One API key the selected pipeline needs but the environment lacks."""

    var: str
    purpose: str
    console_url: str


def _llm_stages_enabled(options: TranscribeOptions) -> bool:
    return any(
        (
            options.format,
            options.identify_speakers,
            options.insert_section_headings,
            options.research_paras,
            options.add_summary_bullets,
            options.add_description,
            options.extract_concepts,
        )
    )


def missing_api_keys(options: TranscribeOptions, workspace_root: Path) -> list[MissingKey]:
    """
    Report keys the selected pipeline needs that are absent from the environment.

    Call after kash setup so `.env` files are already loaded. A custom (non-built-in)
    model profile skips the LLM check since its provider is unknown.
    """
    missing: list[MissingKey] = []
    if not os.environ.get("DEEPGRAM_API_KEY"):
        missing.append(
            MissingKey(
                var="DEEPGRAM_API_KEY",
                purpose="speech-to-text transcription",
                console_url="https://console.deepgram.com/",
            )
        )
    if _llm_stages_enabled(options):
        provider, _ws = get_model_profile(workspace_root)
        if provider is not None:
            var, console_url = _LLM_KEY_BY_PROVIDER[provider]
            if not os.environ.get(var):
                missing.append(
                    MissingKey(
                        var=var,
                        purpose=f"the {provider.value} model profile's LLM stages",
                        console_url=console_url,
                    )
                )
    return missing


def format_missing_keys_message(missing: list[MissingKey]) -> str:
    """A plain-text explanation suitable for people and agents alike."""
    lines = ["Missing API keys for the requested processing:", ""]
    for key in missing:
        lines.append(f"  {key.var}  (needed for {key.purpose}; create one at {key.console_url})")
    lines += [
        "",
        "Keys are loaded automatically from the process environment or from a .env or",
        ".env.local file in the working directory, any parent directory, or your home",
        "directory. Add a line like:",
        "",
        f"  echo '{missing[0].var}=...' >> ~/.env.local",
        "",
        "Then rerun the same command. Run `deep-transcribe --docs` or see",
        f"{DOCS_URL} for full setup steps.",
        "A different provider can be selected with `--models` (see `--help`).",
    ]
    return "\n".join(lines)


## Tests


def test_missing_api_keys_reports_by_pipeline_and_profile(tmp_path: Path) -> None:
    from unittest.mock import patch

    basic = TranscribeOptions.basic()
    annotated = TranscribeOptions.annotated()

    with patch.dict(os.environ, {}, clear=True):
        assert [k.var for k in missing_api_keys(basic, tmp_path)] == ["DEEPGRAM_API_KEY"]
        assert [k.var for k in missing_api_keys(annotated, tmp_path)] == [
            "DEEPGRAM_API_KEY",
            "ANTHROPIC_API_KEY",
        ]

    with patch.dict(
        os.environ,
        {"DEEPGRAM_API_KEY": "dg", "ANTHROPIC_API_KEY": "an"},
        clear=True,
    ):
        assert missing_api_keys(annotated, tmp_path) == []


def test_missing_api_keys_follows_openai_profile(tmp_path: Path) -> None:
    from unittest.mock import patch

    from deep_transcribe.model_profiles import set_model_profile

    set_model_profile(tmp_path, ModelProvider.openai)
    with patch.dict(os.environ, {"DEEPGRAM_API_KEY": "dg"}, clear=True):
        missing = missing_api_keys(TranscribeOptions.annotated(), tmp_path)

    assert [k.var for k in missing] == ["OPENAI_API_KEY"]


def test_format_missing_keys_message_names_vars_and_docs() -> None:
    message = format_missing_keys_message(
        [
            MissingKey(
                "DEEPGRAM_API_KEY", "speech-to-text transcription", "https://console.deepgram.com/"
            )
        ]
    )

    assert "DEEPGRAM_API_KEY" in message
    assert "~/.env.local" in message
    assert "--docs" in message
    assert DOCS_URL in message
