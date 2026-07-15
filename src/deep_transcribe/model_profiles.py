from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path

from kash.llm_utils import LLM


class ModelProvider(StrEnum):
    """Supported LLM provider profiles."""

    anthropic = "anthropic"
    openai = "openai"


@dataclass(frozen=True)
class ModelProfile:
    """Model-role mapping for one provider."""

    provider: ModelProvider
    careful_llm: str
    structured_llm: str
    standard_llm: str
    fast_llm: str

    def as_params(self) -> dict[str, str]:
        """Return the kash workspace parameters for this profile."""
        values = asdict(self)
        del values["provider"]
        return values


MODEL_PROFILES = {
    ModelProvider.anthropic: ModelProfile(
        provider=ModelProvider.anthropic,
        careful_llm=str(LLM.claude_fable_5),
        structured_llm=str(LLM.claude_sonnet_5),
        standard_llm=str(LLM.claude_sonnet_5),
        fast_llm=str(LLM.claude_haiku_4_5),
    ),
    ModelProvider.openai: ModelProfile(
        provider=ModelProvider.openai,
        careful_llm=str(LLM.gpt_5_6_sol),
        structured_llm=str(LLM.gpt_5_6_terra),
        standard_llm=str(LLM.gpt_5_6_terra),
        fast_llm=str(LLM.gpt_5_6_luna),
    ),
}


def set_model_profile(workspace_root: Path, provider: ModelProvider) -> Path:
    """
    Persist a provider profile in the same kash workspace used by Deep Transcribe.

    Existing non-model workspace parameters are preserved.
    """
    from kash.file_storage.persisted_yaml import PersistedYaml

    workspace_root = workspace_root.expanduser().resolve()
    workspace_path = workspace_root / "workspace"
    params_path = workspace_path / ".kash/settings/params.yml"
    params_path.parent.mkdir(parents=True, exist_ok=True)

    params = PersistedYaml(params_path, init_value={})
    current_params = params.read()
    if not isinstance(current_params, dict):
        raise ValueError(f"Invalid workspace model settings: {params_path}")
    params.save(
        {
            **current_params,
            **MODEL_PROFILES[provider].as_params(),
        }
    )

    return workspace_path
