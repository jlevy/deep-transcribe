---
title: Single-Command CLI and SNL Hotel Check-In Example
description: Plan for a hard-cut unified CLI, source-aware prompts, and a reviewed public end-to-end example.
author: Joshua Levy with Codex assistance
---
# Feature: Single-Command CLI and SNL Hotel Check-In Example

**Date:** 2026-08-26 (last updated 2026-08-26)

**Author:** Joshua Levy with Codex assistance

**Status:** In Progress

## Overview

Replace Deep Transcribe’s two-command CLI with one coherent transcription interface and
one comprehensive help page.
The canonical form will be `deep-transcribe [OPTIONS] [SOURCE]`. Model-profile
inspection and selection will move from the `models` subcommand to an optional-value
`--models [PROFILE]` flag.

At the same time, replace the current README walkthrough with the public Saturday Night
Live sketch [Hotel Check In](https://www.youtube.com/watch?v=kq9Q9-U0vrc). The example
will demonstrate how fetched YouTube metadata and one ordinary-prose context description
improve the title, synopsis, outline, and five-speaker labels without asking the user to
author structured metadata.

This is a hard-cut pre-alpha change.
The old `transcribe` and `models` command forms will be removed, not deprecated or
rewritten.

## Goals

- Make `deep-transcribe [OPTIONS] SOURCE` the only transcription command form.
- Put every transcription option, model action, built-in document action, and example on
  one well-grouped `deep-transcribe --help` page.
- Replace the `models` subcommand with `--models [PROFILE]`, using no value to inspect
  profiles and a provider value to select one.
- Keep model selection composable with transcription while retaining workspace-persisted
  settings.
- Include bounded YouTube title, channel, publication date, description, and source URL
  in semantic prompts as untrusted source evidence when the extractor provides them.
- Keep ordinary prose as the normal way to supply reviewed facts about participants,
  characters, chronology, terminology, and desired labels.
- Derive the internal speaker roster from explicit ordinary-prose context when the user
  provides a complete set of speaking roles, without requiring repeated roster flags.
- Publish a reproducible SNL Hotel Check-In walkthrough with correctly attributed
  characters and performers, a concise synopsis, a structural outline, representative
  frame captures, browser-ready HTML, and a high-quality browser-printed PDF.
- Prove that revising context or editorial instructions reuses extraction and raw
  speech-to-text caches.
- Update every human and agent documentation surface to the new CLI contract.

## Non-Goals

- Preserve aliases, argument rewriting, warnings, or other compatibility behavior for
  the removed `transcribe` and `models` subcommands.
- Hard-code any SNL-specific cast, title, summary, or speaker behavior in the product.
- Add runtime web research beyond metadata already returned by the media extractor.
- Require YAML or JSON from an interactive CLI user.
- Treat fetched titles, descriptions, comments, captions, or other source metadata as
  trusted instructions.
- Add a separate PDF renderer or a non-portable commercial printing dependency.
- Change the Deepgram transcription or diarization models as part of this feature.
- Commit draft PDF or screenshot artifacts before their content and print layout have
  been reviewed.

## Background

Deep Transcribe currently exposes `transcribe` and `models` as subcommands while also
supporting a direct-source shorthand.
That produces two help surfaces for the same transcription behavior, a third help
surface for a small model-setting action, argument-routing code, and duplicated examples
throughout the README, built-in guide, skill, tests, and runbook.
The direct form is already the clearest interface, so it should become the complete
interface rather than a shorthand.

The new public fixture is the official Saturday Night Live upload titled “Hotel Check
In.”
Its description identifies a front desk employee played by Kumail Nanjiani and a man
trying to check in played by Mikey Day.
The sketch also includes Beck Bennett, Chris Redd, and Leslie Jones.
The scene has five speaking roles and rapid transitions, making it a useful speaker-
correction and context-propagation test rather than merely a polished screenshot.

Fetched media metadata and user-authored context serve different purposes.
Extractor metadata is useful evidence about the source, but it is untrusted and may be
incomplete or adversarial.
User context is reviewed, trusted source guidance written in ordinary prose.
Processing instructions remain a separate trusted channel because they ask models to
change the shape or emphasis of the output rather than describe the recording.

## Design

### Unified command contract

The public usage becomes:

```text
deep-transcribe [OPTIONS] [SOURCE]
```

`SOURCE` accepts a YouTube or other media URL, or a local audio or video file.
It is optional at parse time only because help, version, built-in documentation, skill
installation, and model-profile actions do not need a source.
After parsing, the CLI will require a source unless a no-source action was requested.
With no arguments, the CLI prints the complete help page and exits successfully.

The parser will have no subparsers, command destination, direct-parser fork, command
registry, or first-argument routing logic.
The removed command words receive no special compatibility behavior.

The single help page will group options in this order:

1. Source and common processing presets.
2. Natural-language context and processing instructions.
3. Exact and structured overrides for automation.
4. Models, workspace, execution, caching, and output.
5. Built-in documentation and agent-skill actions.

Its epilog will explain processing stages, the distinction between source context and
processing instructions, normal incremental reruns, forced reruns, and a small set of
copyable examples. Every example will use the same direct-source syntax.

### Model-profile flag

The `models` subcommand and its `--set` option will be replaced by one optional-value
flag:

```shell
deep-transcribe --models
deep-transcribe --models anthropic
deep-transcribe --models openai --workspace ./other-output
deep-transcribe --models openai URL
```

The behavior is:

- `--models` with no value lists the available profiles and the active/default selection
  for the chosen workspace, then exits.
- `--models PROFILE` persists that profile in the chosen workspace.
- `--models PROFILE` without a source prints confirmation and exits.
- `--models PROFILE SOURCE` persists the profile and continues the transcription in the
  same invocation.
- `--models` with no profile and a source is an error because listing and transcribing
  are separate actions.
- `--json` gives stable structured output for a no-source model action and retains its
  existing final-artifact meaning during transcription.

Only the supported `anthropic` and `openai` profile names are accepted.
Help text will make the optional value and persistence behavior explicit.

### Source-aware semantic context

For URL sources, retain the extractor’s useful descriptive fields on the source item and
propagate them through cached transcript items before semantic processing.
When available, prompts may receive a bounded representation of:

- source title;
- channel or uploader;
- publication date;
- source description;
- canonical source URL.

The prompt will delimit this material as source metadata and explicitly treat it as
reference evidence, never as instructions.
User-authored `--context` prose is merged as reviewed source guidance through the
existing `additional_context` field.
User-authored `--instructions` remains trusted only by the synopsis and outline stages.

The implementation must first verify which YouTube fields Kash already persists and
which Deep Transcribe prompts already receive through `Item.prompt_context()`. It should
add only the missing propagation or normalization locally.
Any upstream change requires evidence that the missing behavior belongs to a reusable
Kash primitive rather than this product’s prompt contract.

### Prose-to-roster interpretation

When user-authored context explicitly describes a complete set of speaking characters or
roles, a structured model step will convert that prose into Deep Transcribe’s internal
speaker roster and label notes before merged-boundary correction.
The user’s human interface remains a paragraph such as “There are five speaking roles,”
followed by the character, role, and performer relationships.

The interpretation must be conservative:

- Extract only participants and relationships supported by the supplied context.
- Return no inferred roster when the prose does not clearly claim completeness.
- Never add a person merely because fetched metadata lists them in a cast or channel
  description.
- Treat explicit `--speaker-role` values as the authoritative roster and skip roster
  inference when they are present.
- Apply exact `--speaker ID=NAME` mappings after inference as authoritative provider-ID
  overrides.

The structured result is internal metadata, not a new user-facing format.
It participates in semantic cache identity, so a changed context paragraph reruns the
model-dependent speaker stages while preserving the raw Deepgram transcript.
This makes one prose description sufficient for the SNL example without weakening the
existing fail-closed correction behavior.

### Reviewed SNL example context

The example will use one readable prose value containing the reviewed facts and desired
speaker-label policy.
It will identify:

- Mr. Adams, played by Mikey Day;
- the front desk employee, played by Kumail Nanjiani;
- the government representative, played by Beck Bennett;
- the two unnamed Room 904 guests, played by Chris Redd and Leslie Jones.

Named fictional characters or clear roles should be the primary transcript labels.
Performer names may disambiguate unnamed roles and should appear in the synopsis, but
the system must not swap performers and characters or invent names unsupported by the
source. The expected setup is that Adams has just returned from North Korea and wants to
reach his room while the front desk employee repeatedly promotes hotel amenities.

The CLI example will demonstrate ordinary prose, not a YAML metadata file.
Exact speaker IDs remain an optional correction tool only if the first reviewed output
shows that provider diarization made them necessary.

### Backward compatibility requirements

- **CLI contract:** DO NOT MAINTAIN. The project is pre-alpha, the user requested a hard
  cut, and all owned documentation, skills, tests, and examples can move together.
- **Internal code:** DO NOT MAINTAIN. Delete the subparser and direct-parser branches
  rather than retaining dormant routing paths.
- **Library APIs:** N/A. This plan changes the executable interface, not a supported
  Python library contract.
- **Server APIs:** N/A. Deep Transcribe has no server interface in scope.
- **Plugin and extension APIs:** N/A. The self-installing skill is documentation and is
  regenerated with the CLI.
- **File formats:** MAINTAIN. Existing workspace, cache, transcript, and HTML formats do
  not change; only the contents of the public example artifacts are replaced.
- **Persisted client state:** MAINTAIN. Existing Kash workspace model settings and
  transcription caches remain readable because their storage shape does not change.
- **Database schemas:** N/A.

### README and artifacts

The README will use the SNL sketch as the main end-to-end example and remove the
previous hotel walkthrough and artifacts.
It will show the concise CLI first, followed by a compact two-column showcase:

- a clickable video thumbnail linked to the official YouTube upload;
- a clickable transcript preview linked to the reviewed PDF;
- direct text links to the video and PDF below the images.

The final transcript should have a source-aware title, a brief synopsis broken into
readable paragraphs, a clean sans-serif section outline with section-aligned key points,
correct speaker labels, subtle bracketed timestamps, representative frames, and the Deep
Transcribe footer.
The static HTML must remain the source of truth and print cleanly from
an ordinary Chrome or Chromium browser with no special renderer.

Candidate HTML, PDF, and screenshot files will remain outside the commit until visual
and content review passes.
The approved files will then replace the existing example artifacts under
`docs/examples/`.

### Documentation surfaces

The hard cut must update all authored and generated surfaces together:

- `README.md`;
- `deep-transcribe --help` and its module-level usage text;
- the packaged `deep-transcribe --docs` guide;
- the canonical packaged `SKILL.md` and every generated skill mirror;
- installation and context-design documentation where the public contract is named;
- the end-to-end runbook;
- parser, help, docs, skill-drift, and end-to-end tests.

No checked-in text may continue to teach `deep-transcribe transcribe`,
`deep-transcribe models`, `models --set`, or command-specific help.

## Implementation Plan

### Phase 1: Executable contract and focused tests

- [x] Add failing parser and subprocess tests for the single command, optional target,
  one-page help, model list/set/continue behavior, JSON behavior, and no-source errors.
- [x] Replace the subparser and direct-parser architecture with one parser and one
  dispatch path.
- [x] Implement `--models [PROFILE]`, including active workspace reporting and
  persistence before an optional transcription.
- [x] Remove the old command builders, routing constants, command destination, and
  duplicated help text as a hard cut.
- [ ] Update all CLI examples, built-in documentation, the canonical skill, generated
  mirrors, and unit tests; assert that legacy syntax has disappeared.

### Phase 2: Source context and public fixture

- [ ] Audit YouTube metadata from extraction through cached transcript items and
  semantic prompts, then add focused tests for the bounded untrusted context that is
  actually missing.
- [ ] Add conservative structured extraction of a complete speaker roster from explicit
  ordinary-prose context, with exact roster and speaker-ID overrides taking precedence.
- [ ] Verify the SNL cast and character mapping from the official upload and a script or
  transcript source, then write the one-paragraph example context.
- [ ] Run the annotated public fixture end to end and review the title, synopsis,
  outline, all five speaker labels, timestamps, frames, HTML, and cache records.
- [ ] Make one context or editorial-instruction refinement and prove the rerun reuses
  the extraction and raw Deepgram transcript.
- [ ] Browser-print the final HTML, inspect the rendered PDF, capture the README
  preview, and replace the old public example only after review.
- [ ] Run focused tests, the full quality gate, package builds, skill drift validation,
  and the public end-to-end runbook before opening the pull request.

## Implementation Beads

Epic `dt-qzym` tracks this spec.
Its implementation beads follow the plan’s execution order:

- [x] `dt-ojgn`: Define the single-command CLI contract with failing tests.
- [x] `dt-0o6v`: Implement the unified parser and `--models` flag; blocked by `dt-ojgn`.
- [ ] `dt-t7oj`: Audit and complete YouTube source-context propagation; blocked by
  `dt-ojgn`.
- [ ] `dt-vot2`: Infer speaker rosters from ordinary-prose context; blocked by
  `dt-ojgn`.
- [ ] `dt-ifou`: Update every help, documentation, and skill surface; blocked by
  `dt-0o6v`.
- [ ] `dt-g641`: Run the SNL fixture and prove cache-aware refinement; blocked by
  `dt-0o6v`, `dt-t7oj`, and `dt-vot2`.
- [ ] `dt-bqft`: Publish the reviewed SNL Hotel Check-In README showcase; blocked by
  `dt-ifou` and `dt-g641`.
- [ ] `dt-7res`: Validate the hard cut and prepare the pull request; blocked by
  `dt-bqft`.

## Testing Strategy

Use focused, test-driven changes for the public CLI contract.
Parser and subprocess tests will cover all no-source actions, normal transcription,
model-profile inspection, persistent selection, selection plus transcription, invalid
profiles, workspace selection, JSON output, no-argument help, and missing-source errors.
The top-level help test will assert one usage line, the intended option-group ordering,
incremental-rerun guidance, and the absence of a command directory.

Metadata tests will use synthetic items so they can prove that fetched metadata is
bounded, delimited, propagated through a raw transcript cache hit, and ignored as
instructions without network calls.
Prompt tests will preserve the distinction between source evidence and trusted
processing instructions.
Structured-output tests will prove that explicit complete prose yields the intended
roster, ambiguous prose yields no roster, fetched cast lists alone do not create a
roster, and exact CLI overrides take precedence.

The live SNL validation will record the source item, raw transcript item, final
transcript, HTML, and Deepgram-call count.
Acceptance requires all five speaking roles to be distinguishable at their actual turns,
performer references to be accurate, the synopsis to identify the SNL sketch and
premise, and the outline to follow the sketch’s progression.
A context-only or instruction-only second run must not call Deepgram again.

Visual validation will use Chrome or Chromium print-to-PDF, render every PDF page to an
image, and inspect the title block, synopsis paragraphs, outline bullets, timestamps,
frame placement, page breaks, and footer.
The README thumbnail and PDF links must resolve from GitHub’s rendered README.

Before handoff, run `make lint-check`, `make test`, `make build`, the generated-skill
drift checks, and the relevant release smoke tests.

## Rollout Plan

Land the hard cut and public fixture in one pull request after the existing README
showcase work is incorporated or superseded.
Because this is pre-alpha, publish the next patch release with no deprecation period.
Smoke-test the installed release with direct transcription help, model listing,
workspace model selection, built-in docs, skill installation, and the public SNL example
command.

## Open Questions

None.
The optional-value `--models [PROFILE]` contract, hard removal of both subcommands,
ordinary-prose context, and SNL example source are fixed by this plan.

## References

- [Official SNL upload: Hotel Check In](https://www.youtube.com/watch?v=kq9Q9-U0vrc)
- [SNL Transcripts Tonight: Hotel Check In](https://snltranscripts.jt.org/17/hotel-check-in.phtml)
- Existing context architecture: `docs/transcription-context-design.md`
- Built-in operational guide: `src/deep_transcribe/resources/docs.md`
- Canonical skill: `src/deep_transcribe/resources/skill/SKILL.md`

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
