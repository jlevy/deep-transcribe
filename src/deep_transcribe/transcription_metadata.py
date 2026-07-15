from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from textwrap import dedent
from typing import Any, cast

from frontmatter_format import from_yaml_string
from kash.file_storage.file_store import FileStore
from kash.model import Item, ItemType
from sidematter_format import Sidematter

TRANSCRIPTION_METADATA_KEY = "transcription"


@dataclass(frozen=True)
class TranscriptionMetadata:
    """
    User-supplied metadata that augments source metadata before transcription.

    `extra` stays extensible while Deep Transcribe normalizes the currently recognized
    `extra.transcription` fields.
    """

    title: str | None = None
    description: str | None = None
    additional_context: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def merged_with(self, other: TranscriptionMetadata) -> TranscriptionMetadata:
        """Merge metadata with nonempty values from `other` taking precedence."""
        return TranscriptionMetadata(
            title=other.title if other.title is not None else self.title,
            description=other.description if other.description is not None else self.description,
            additional_context=(
                other.additional_context
                if other.additional_context is not None
                else self.additional_context
            ),
            extra=_deep_merge(self.extra, other.extra),
        )

    @property
    def key_terms(self) -> list[str]:
        transcription = self.extra.get(TRANSCRIPTION_METADATA_KEY)
        if not isinstance(transcription, dict):
            return []
        terms = cast(dict[str, Any], transcription).get("key_terms")
        if not isinstance(terms, list):
            return []
        return [term for term in cast(list[object], terms) if isinstance(term, str)]

    @property
    def speaker_roster(self) -> list[str]:
        transcription = self.extra.get(TRANSCRIPTION_METADATA_KEY)
        if not isinstance(transcription, dict):
            return []
        roster = cast(dict[str, Any], transcription).get("speaker_roster")
        if not isinstance(roster, list):
            return []
        return [label for label in cast(list[object], roster) if isinstance(label, str)]


def _deep_merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in updates.items():
        existing = result.get(key)
        if isinstance(value, dict) and isinstance(existing, dict):
            result[key] = _deep_merge(
                cast(dict[str, Any], existing),
                cast(dict[str, Any], value),
            )
        else:
            result[key] = deepcopy(cast(object, value))
    return result


def _optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"`{field_name}` must be a string")
    value = value.strip()
    return value or None


def _normalize_key_terms(value: object) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("`key_terms` must be a YAML list of strings")
    terms = cast(list[object], value)
    if not all(isinstance(term, str) for term in terms):
        raise ValueError("`key_terms` must contain only strings")
    string_terms = cast(list[str], terms)
    return list(dict.fromkeys(term.strip() for term in string_terms if term.strip()))


def _normalize_speaker_hints(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError("`speaker_hints` must map speaker IDs to names")
    hints: dict[str, str] = {}
    for speaker_id, name in cast(dict[object, object], value).items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("`speaker_hints` names must be nonempty strings")
        hints[str(speaker_id)] = name.strip()
    return hints


def normalize_speaker_roster(value: object) -> list[str]:
    """Validate and normalize a complete speaker roster."""
    if not isinstance(value, list):
        raise ValueError("`speaker_roster` must be a YAML list of speaker names or roles")
    roster = cast(list[object], value)
    if not all(isinstance(label, str) and label.strip() for label in roster):
        raise ValueError("`speaker_roster` must contain only nonempty strings")
    normalized = list(dict.fromkeys(cast(str, label).strip() for label in roster))
    if len(normalized) < 2:
        raise ValueError("`speaker_roster` must contain at least two distinct speakers")
    label_keys = [re.sub(r"[\W_]+", "", label.casefold()) for label in normalized]
    if any(not key for key in label_keys) or len(set(label_keys)) != len(label_keys):
        raise ValueError("`speaker_roster` labels must be distinct names or roles")
    return normalized


def transcription_metadata_from_mapping(data: object) -> TranscriptionMetadata:
    """Validate and normalize a YAML/JSON transcription metadata object."""
    if not isinstance(data, dict):
        raise ValueError("Transcription metadata must be a YAML or JSON mapping")
    data_dict = cast(dict[str, object], data)

    allowed_fields = {
        "title",
        "description",
        "additional_context",
        "extra",
        "key_terms",
        "speaker_hints",
        "speaker_roster",
    }
    unexpected_fields = sorted(str(key) for key in data_dict if key not in allowed_fields)
    if unexpected_fields:
        raise ValueError(f"Unsupported transcription metadata fields: {unexpected_fields}")

    raw_extra = data_dict.get("extra", {})
    if not isinstance(raw_extra, dict):
        raise ValueError("`extra` must be a mapping")
    extra = deepcopy(cast(dict[str, Any], raw_extra))

    raw_transcription = extra.get(TRANSCRIPTION_METADATA_KEY, {})
    if not isinstance(raw_transcription, dict):
        raise ValueError("`extra.transcription` must be a mapping")
    transcription = deepcopy(cast(dict[str, Any], raw_transcription))

    if "key_terms" in transcription:
        transcription["key_terms"] = _normalize_key_terms(transcription["key_terms"])
    if "speaker_hints" in transcription:
        transcription["speaker_hints"] = _normalize_speaker_hints(transcription["speaker_hints"])
    if "speaker_roster" in transcription:
        transcription["speaker_roster"] = normalize_speaker_roster(transcription["speaker_roster"])
    if "key_terms" in data_dict:
        transcription["key_terms"] = _normalize_key_terms(data_dict["key_terms"])
    if "speaker_hints" in data_dict:
        transcription["speaker_hints"] = _normalize_speaker_hints(data_dict["speaker_hints"])
    if "speaker_roster" in data_dict:
        transcription["speaker_roster"] = normalize_speaker_roster(data_dict["speaker_roster"])
    if transcription or TRANSCRIPTION_METADATA_KEY in extra:
        extra[TRANSCRIPTION_METADATA_KEY] = transcription

    return TranscriptionMetadata(
        title=_optional_text(data_dict.get("title"), "title"),
        description=_optional_text(data_dict.get("description"), "description"),
        additional_context=_optional_text(
            data_dict.get("additional_context"), "additional_context"
        ),
        extra=extra,
    )


def parse_transcription_metadata(text: str) -> TranscriptionMetadata:
    """Parse inline YAML or JSON transcription metadata."""
    return transcription_metadata_from_mapping(from_yaml_string(text))


def load_transcription_metadata(path: Path) -> TranscriptionMetadata:
    """Load transcription metadata from a UTF-8 YAML or JSON file."""
    return parse_transcription_metadata(path.read_text(encoding="utf-8"))


def apply_transcription_metadata(item: Item, metadata: TranscriptionMetadata) -> Item:
    """Apply user metadata to an item in place and return it."""
    if metadata.title is not None:
        item.title = metadata.title
    if metadata.description is not None:
        item.description = metadata.description
    if metadata.additional_context is not None:
        item.additional_context = metadata.additional_context
    if metadata.extra:
        item.extra = _deep_merge(item.extra or {}, metadata.extra)
    return item


def get_speaker_roster(item: Item) -> list[str]:
    """Read Deep Transcribe's speaker roster from the extensible item metadata payload."""
    item_extra = cast(dict[str, object], item.extra or {})
    raw_transcription = item_extra.get(TRANSCRIPTION_METADATA_KEY)
    raw_roster = (
        cast(dict[object, object], raw_transcription).get("speaker_roster")
        if isinstance(raw_transcription, dict)
        else None
    )
    if not isinstance(raw_roster, list):
        return []
    return [
        label.strip()
        for label in cast(list[object], raw_roster)
        if isinstance(label, str) and label.strip()
    ]


def copy_source_metadata(source: Item, target: Item) -> Item:
    """Copy descriptive source metadata to another item without losing target metadata."""
    if source.title is not None:
        target.title = source.title
    if source.description is not None:
        target.description = source.description
    if source.additional_context is not None:
        target.additional_context = source.additional_context
    if source.extra:
        target.extra = _deep_merge(target.extra or {}, source.extra)
    return target


def persist_item_metadata(item: Item, workspace: FileStore) -> None:
    """
    Persist item metadata so kash cache keys reflect later corrections.

    Text resources store metadata in frontmatter. Binary resources keep bytes intact and
    use sidematter metadata, which kash includes in the action input hash.
    """
    if not item.store_path:
        raise ValueError("Cannot persist metadata for an unsaved item")
    if item.format and item.format.supports_frontmatter:
        workspace.save(item, overwrite=True)
    else:
        path = workspace.base_dir / item.store_path
        Sidematter(path).write_meta(item.metadata(), formats="all", make_parents=True)


## Tests


def test_transcription_metadata_normalizes_merges_and_applies() -> None:
    parsed = parse_transcription_metadata(
        dedent("""
            title: Product interview
            additional_context: Alice is the host.
            key_terms: [SignalFlow, SignalFlow, Nova Prime]
            speaker_hints:
              0: Alice Chen
            speaker_roster: [Alice Chen, Bob Diaz]
            extra:
              transcription:
                future_option: true
            """).strip()
    )
    override = transcription_metadata_from_mapping(
        {
            "additional_context": "Alice Chen interviews Bob Diaz.",
            "speaker_hints": {"1": "Bob Diaz"},
        }
    )
    item = Item(type=ItemType.doc, extra={"transcription": {"existing_option": True}})

    apply_transcription_metadata(item, parsed.merged_with(override))

    assert item.title == "Product interview"
    assert item.additional_context == "Alice Chen interviews Bob Diaz."
    assert item.extra == {
        "transcription": {
            "existing_option": True,
            "future_option": True,
            "key_terms": ["SignalFlow", "Nova Prime"],
            "speaker_hints": {"0": "Alice Chen", "1": "Bob Diaz"},
            "speaker_roster": ["Alice Chen", "Bob Diaz"],
        }
    }


def test_speaker_roster_rejects_ambiguous_duplicate_labels() -> None:
    try:
        transcription_metadata_from_mapping({"speaker_roster": ["Mr. Adams", "Mr Adams"]})
    except ValueError as error:
        assert "distinct names or roles" in str(error)
    else:
        raise AssertionError("Equivalent speaker labels must be rejected")
