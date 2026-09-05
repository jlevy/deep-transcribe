---
title: Agent Iteration Loop
description: Make the review-and-correct loop the tool's normal use, so an agent can run a source, read what it produced without a browser, adjust through flags and a checked-in recipe, and rerun only what changed.
author: Joshua Levy with Claude assistance
---
# Feature: Agent Iteration Loop

**Date:** 2026-09-04

**Author:** Joshua Levy with Claude assistance

**Status:** Draft

## Overview

The first run of a five-hour recording is a draft. The result the owner wants comes from
reading that draft, noticing what is wrong, changing an input, and rerunning only the
stages that depend on it. The docs already describe this loop, and the cache already
makes it cheap. What is missing is that every step between "run" and "rerun" assumes a
person with a browser: there is no way to read what a run produced, no way to rebuild
the page without rerunning, and two of the largest quality levers have no flag at all.

This plan makes the loop first-class: a recipe that reproduces a result, a report an
agent can read, and flags for the corrections that today need a hand-written script.

## Goals

- An agent can take a source from first run to reviewed result using only the CLI and
  the files in a recipe directory, with no code and no browser.
- Every correction made by hand on Lex #501 during stabilization has a flag or a recipe
  field, and the cost of each is documented from measurement.
- The Lex #501 recipe in `docs/examples/lex-501/` is the worked example and the
  regression check.

## Non-Goals

- New analysis stages beyond those the corrections require.
- A GUI or a review web app. The loop is the CLI plus files an agent can read and edit.

## Background

### What exists

- `docs.md`, "Iterate Without Repeating Speech-to-Text": the loop, the rerun table with
  the measured cost of each kind of change, "Correct a Reviewed Result", and an agent
  prompt pattern.
- The flags: `--context`, `--context-file`, `--instructions`, `--segments` (with `none`
  to clear), `--key-term`, `--speaker`, `--speaker-role`, `--metadata`,
  `--rerun-processing`, `--rerun`, `--json`.
- `--metadata YAML` accepts title, description, context, key terms, roster, instructions
  and segments in one file, which makes a recipe a single editable artifact.
- The cache resumes at the first affected stage. Measured on Lex #501: an unchanged
  rerun is 13 s; editing an existing hint is 20 min; new key terms re-run
  speech-to-text.

### What was needed and did not exist

Every one of these was done today with a one-off Python script or a browser:

| need | what was done by hand | bead |
| --- | --- | --- |
| know what a run produced: headings, themes, segments, spellings | scripts over the item YAML and the DOM | dt-i6mg |
| rebuild the page after a template or `--elements` change | a script calling `format_results` | dt-269j |
| choose key terms | a capitalized-token frequency scan found Omarchy spelled three ways about eighty times | dt-i6mg |
| fewer section headings: 206 on five hours, one per 1.5 min | nothing; no flag reaches that stage | dt-21df |
| stop 498 one-word "Mhmm" turns rendering as paragraphs | nothing | dt-aueh |
| verify the page | a browser with an emulated viewport | dt-i6mg covers the counts; the browser stays for layout |

The spelling scan is the clearest case: `--key-term` exists, but without a list of
variants there is no way to know which terms to pass short of reading five hours of
transcript.

## Design

### Approach

Three pieces, in dependency order. The report and the re-export make the loop closable
by an agent and cost little; the quality levers are what the loop then turns.

1. **Recipe.** A directory per source holding `metadata.yml` (everything `--metadata`
   accepts), `segments.yml`, and a README with the one command and the measured cost of
   changing each part. `docs/examples/lex-501/` is the first. The docs' iteration
   section points at it as the pattern.
2. **Report** (`--report`, text and JSON). From the final item: section headings with
   count and density; outline entry count; theme names with concept counts; segments in
   effect with spans and whether each is suppressed; speaker label counts; frames kept
   of captured; and the top proper-noun spelling variants with counts. The loop becomes
   run, read the report, edit the recipe, rerun.
3. **Levers.** `--export-only` to rebuild the page from the cached final item; a
   section-heading density target with publisher chapters as the skeleton where they
   exist; back-channel folding on by default with `--keep-backchannel` to disable.

### Components

- `cli_main.py`: `--report`, `--export-only`, `--keep-backchannel`, the density flag.
- `transcribe_commands.py`: the report over the final item; export-only path.
- A new heading-consolidation stage and a chapter fetch (kash's YouTube metadata does
  not carry chapters today).
- `transcript_spacing.py` or a sibling: back-channel folding.
- `docs.md` and the agent skill: the iteration section gains the recipe and the report;
  the rerun table gains rows for the new flags.

### API Changes

New flags: `--report`, `--export-only`, `--keep-backchannel`, and a heading-density
option. No change to existing flag semantics.

## Implementation Plan

### Phase 1: Close the loop

- [x] `--report` over the final item, text and JSON, including spelling variants.
  (dt-i6mg)
- [x] `--export-only`. (dt-269j)
- [x] Docs: point the iteration section at `docs/examples/lex-501/`; add the report to
  the loop; add rerun-table rows for the new flags; update the skill's "Iterate on a
  Reviewed Result".

### Phase 2: The quality levers

- [x] Back-channel folding, default on. Measure turn count before and after on Lex #501.
  (dt-aueh)
- [x] Publisher chapters as the H2 skeleton, model headings demoted to H3. The index,
  outline and timeline already read only H2, so no downstream change is needed; Lex #501
  goes from 206 sections to 23. A density cap for sources without chapters is a
  follow-on. (dt-21df)
- [x] Recipe replacements after speech-to-text; Omachi 19 → 0 on the real transcript.
  (dt-il5d)
- [x] Rerun the Lex #501 recipe and record the result in its README.
- [x] `--rerun-from STAGE`: set a stage's cached results aside and rerun, for the case
  where a stage's code changed. Refuses `transcribe`. (dt-8cd9)

## Testing Strategy

Each flag gets a test that drives the CLI path, not a helper, and is checked against the
reverted change. The Lex #501 recipe is the end-to-end check: after Phase 2 its README
records the report output, and a rerun of the recipe must reproduce those counts within
model variance.

## Rollout Plan

Phase 1 lands on PR #19's branch or a follow-on PR; Phase 2 follows. The recipe README
is updated with each measured result.

## Open Questions

- Should back-channel folding drop the turn or keep it as a bracketed aside inside the
  previous paragraph? Dropping loses nothing a reader wants; keeping preserves the
  timestamp.
- Heading density default: one per five minutes gives about sixty headings on five
  hours; one per eight gives about forty. Pick after seeing both on Lex #501.

## References

- `plan-2026-09-04-long-form-stabilization.md`
- `plan-2026-09-04-transcript-segments.md`
- `docs/examples/lex-501/README.md`

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
