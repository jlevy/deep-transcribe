# Transcription Context and Package Boundaries

Deep Transcribe owns transcription orchestration, CLI behavior, presets, and its
feature-specific metadata schema. The kash packages provide stable, reusable primitives.
This keeps most Deep Transcribe features local and avoids lockstep releases across the
dependency chain.

## Metadata model

Source items use the existing `title` and `description` fields plus the generic
`additional_context` field supplied by kash. Semantic actions may use those fields as
bounded reference material, but must never treat fetched metadata as instructions.

Transcription-specific data is stored in the existing namespaced `Item.extra` mapping:

```yaml
title: Acme weekly product review
description: Recording of the July product meeting.
additional_context: |
  Alice Chen facilitates. Bob Diaz presents product metrics.
extra:
  transcription:
    key_terms:
      - Alice Chen
      - Bob Diaz
      - SignalFlow
    speaker_hints:
      "0": Alice Chen
      "1": Bob Diaz
```

The `extra.transcription` mapping is an extensible payload. Kash core preserves it without
knowing its schema. Kash-media consumes the fields it understands and ignores unknown fields,
so Deep Transcribe can add local metadata without changing kash core.

## Package responsibilities

- **kash-shell:** Persist generic additional context and provide an opt-in helper for adding
  bounded item metadata to semantic model prompts. Item cache hashes include resolved
  sidematter metadata so binary resources respond to metadata changes.
- **kash-docs:** Opt relevant semantic actions into generic item context. Mechanical text
  transforms remain context-free.
- **kash-media:** Provide stable transcription and speaker-identification primitives, consume
  recognized `extra.transcription` hints, and include transcription settings in cache identity.
- **Deep Transcribe:** Parse and validate metadata files, enrich source items, own presets and
  rerun behavior, and expose the complete workflow through its CLI, MCP actions, and skill.

Deep Transcribe accepts a metadata file plus concise context, key-term, and speaker flags.
The MCP preset actions accept the same schema as inline YAML or JSON through
`metadata_yaml`. A semantic-only correction changes downstream action hashes while reusing
the cached raw transcript. A key-term change is part of the Deepgram settings cache identity
and intentionally requests a new transcript. `--rerun-processing` provides an explicit
downstream-only refresh for model-profile changes and quality checks; full `--rerun` is
reserved for intentionally refreshing speech-to-text.

Deep Transcribe should implement presentation, workflow, and optional feature changes locally.
Upstream changes are reserved for reusable primitives, provider integrations, or defects in a
shared action.

## Dependency policy

First-party packages use bounded compatible ranges within the current pre-1.0 minor line:

```text
kash-docs:       kash-shell >=0.4.4,<0.5
kash-media:      kash-docs >=0.2.3,<0.3
deep-transcribe: kash-media >=0.4.3,<0.5
```

The lower bound records the API version actually required. The upper bound prevents accidental
adoption of a potentially breaking pre-1.0 minor release. A new kash-shell patch can therefore
flow into downstream lockfiles without requiring new kash-docs or kash-media releases unless
their own code must change.

## Release gate

Changes are tested against local editable dependencies first. Publishing happens only after the
short-video end-to-end quality gate passes. Required releases are patch increments and are
published in dependency order; downstream projects are then resolved again without local source
overrides.
