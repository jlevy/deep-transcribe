# Transcription Context and Package Boundaries

Deep Transcribe owns transcription orchestration, CLI behavior, presets, and its
feature-specific metadata schema.
The kash packages provide stable, reusable primitives.
This keeps most Deep Transcribe features local and avoids lockstep releases across the
dependency chain.

## Prose Interface and Metadata Model

The human CLI is prose-first.
`--context` and `--context-file` accept ordinary descriptions of participants, roles,
chronology, terminology, and other source facts.
The speaker-identification action combines that prose with the transcript and returns a
structured speaker-ID mapping internally.
When the prose clearly claims a complete set of speaking roles, Deep Transcribe first
uses a conservative structured step to derive the internal roster needed for merged-
boundary correction.
Incomplete participant descriptions fail closed and continue with the provider-level
identification path.
Users provide structured metadata only for automation or exact overrides.

Source items use the existing `title` and `description` fields plus the generic
`additional_context` field supplied by kash.
Deep Transcribe renders an allow-listed, bounded source-evidence block that can also
include the canonical URL and available channel and publication fields retained by the
extractor. Semantic actions must never treat fetched metadata as instructions.

User-authored `processing_instructions` are a separate trusted channel for requested
output structure, emphasis, and level of detail.
The parser stores this field under `extra.transcription`; only Deep Transcribe actions
that explicitly support instructions follow it.
Deep Transcribe removes the field while running speaker correction, formatting, and
section generation, then restores it before the overview actions.
An instruction-only rerun therefore starts at the synopsis and outline rather than
invalidating unrelated semantic work.

Transcription-specific data is stored internally in the existing namespaced `Item.extra`
mapping:

```yaml
title: Acme weekly product review
description: Recording of the July product meeting.
additional_context: |
  Alice Chen facilitates. Bob Diaz presents product metrics.
processing_instructions: |
  Keep the synopsis brief. Emphasize decisions and open questions in the outline.
extra:
  transcription:
    key_terms:
      - Alice Chen
      - Bob Diaz
      - SignalFlow
    speaker_hints:
      "0": Alice Chen
      "1": Bob Diaz
    speaker_roster:
      - Alice Chen
      - Bob Diaz
```

The `extra.transcription` mapping is an extensible payload.
Kash core preserves it without knowing its schema.
Kash-media consumes the fields it understands and ignores unknown fields, so Deep
Transcribe can add local metadata without changing kash core.

`speaker_hints` rename trustworthy provider IDs directly.
`speaker_roster` is the internal complete list of known speaking roles for recordings
where provider diarization merged distinct voices.
It may come from an exact automation override or from conservative interpretation of
complete ordinary-prose context.
Deep Transcribe owns the roster-based boundary-correction stage: it uses the workspace’s
careful model profile to assign each timestamped utterance to an exact roster label
without rewriting transcript text, rejects uncertain or unknown assignments, and
preserves the raw provider transcript for review.
Use descriptive `additional_context` to distinguish roles by chronology, subject matter,
or forms of address.
Include exact dialogue transition cues when brief interjections are ambiguous.
Do not add silent people to the roster.
Long transcripts are processed in overlapping windows.
Stable overlap assignments become consensus; disagreements receive a focused
adjudication pass with neighboring turns and source context.
An uncertain adjudication still fails closed instead of choosing a label.

## Package Responsibilities

- **kash-shell:** Persist generic additional context and provide an opt-in helper for
  adding bounded item metadata to semantic model prompts.
  Item cache hashes include resolved sidematter metadata so binary resources respond to
  metadata changes.
- **kash-docs:** Opt relevant semantic actions into generic item context.
  Mechanical text transforms remain context-free.
- **kash-media:** Provide stable transcription and speaker-identification primitives,
  consume recognized `extra.transcription` hints, and include transcription settings in
  cache identity.
- **Deep Transcribe:** Parse and validate metadata files, render bounded source
  evidence, derive a complete speaker roster from explicit prose, correct merged speaker
  boundaries, own presets and rerun behavior, and produce the transcript-specific
  synopsis and structural outline.
  It exposes the complete workflow through its self-documenting CLI and installable
  skill.

Deep Transcribe accepts natural-language context and processing instructions as its
primary human interface, plus simple title, description, key-term, and speaker override
flags. A metadata file exposes the same structure for automation.
Internal preset actions accept the same schema as inline YAML or JSON through
`metadata_yaml`. A semantic-only correction changes downstream action hashes while
reusing the cached raw transcript.
A key-term change is part of the Deepgram settings cache identity and intentionally
requests a new transcript.
`--rerun-processing` provides an explicit downstream-only refresh for model-profile
changes and quality checks; full `--rerun` is reserved for intentionally refreshing
speech-to-text.

Deep Transcribe should implement presentation, workflow, and optional feature changes
locally.
Upstream changes are reserved for reusable primitives, provider integrations, or
defects in a shared action.

## Dependency Policy

First-party packages use bounded compatible ranges within the current pre-1.0 minor
line:

```text
kash-docs:       kash-shell >=0.4.4,<0.5
kash-media:      kash-docs >=0.2.3,<0.3
deep-transcribe: kash-media >=0.4.3,<0.5
```

The lower bound records the API version actually required.
The upper bound prevents accidental adoption of a potentially breaking pre-1.0 minor
release. A new kash-shell patch can therefore flow into downstream lockfiles without
requiring new kash-docs or kash-media releases unless their own code must change.

## Release Gate

Changes are tested against local editable dependencies first.
Publishing happens only after the short-video end-to-end quality gate passes.
Required releases are patch increments and are published in dependency order; downstream
projects are then resolved again without local source overrides.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
