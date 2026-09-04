---
title: Long-Form Stabilization
description: What has to be true, and what has to be fixed, for one command on a five-hour podcast to complete cleanly, produce a legible page, and make every documented rerun claim true.
author: Joshua Levy with Claude assistance
---
# Feature: Long-Form Stabilization

**Date:** 2026-09-04

**Author:** Joshua Levy with Claude assistance

**Status:** Draft

## Overview

Two feature specs on this branch—chunked extraction and transcript segments—built the
machinery for hours-long media. This plan is not a third feature. It is the list of what
must be true for that machinery to work cleanly, end to end, on the recording it was
built for, and the map from each gap to the bead that closes it.

The target is concrete and testable. On Lex Fridman #501 (5 h 15 m, ~2,900 paragraphs):

1. One command completes with exit 0 and no traceback.
2. The page renders correctly in a browser: wrapped timeline rows, about 240 frames
   rather than 502, concepts in roughly a dozen collapsed themes, the outline grouped by
   theme.
3. A rerun with nothing changed costs seconds and no API calls.
4. A rerun with `--segments` excludes the teaser from the concept map, outline and
   synopsis, collapses it in the transcript, and does not repeat speech-to-text or
   speaker correction.
5. Every row of the rerun table in `docs.md` is true as written.

## Goals

- Prove the current code on the full recording, in a browser, not by reading.
- Make every documented claim about scale and reruns match a measurement.
- Close the gaps that turn a two-hour run into a wasted one: disk, error reporting,
  transient failures.
- Leave a written map from each remaining gap to a bead, so nothing is carried in
  memory.

## Non-Goals

- New analysis features: publisher chapters as headings (dt-pq0j), word-level timings
  (dt-qlfx), key terms for proper nouns (dt-l0i3), clustered concept tracks (dt-4zij).
  Each is real and each has its own bead; none is needed for the target above.
- Making the two expensive formatting stages faster. Speaker correction and section
  headings are 65 of the run's 112 minutes. That is a cost problem, not a correctness
  one, and it is out of scope here.

## Background

### What the full recording actually costs

Measured on the one complete, error-free run of #501 (workspace `dt-final`):

| stage | minutes |
| --- | --- |
| transcribe (download + Deepgram) | 12 |
| correct_speaker_turns | 31 |
| break_into_paragraphs | 12 |
| insert_section_headings | 34 |
| add_transcript_outline | 5 |
| insert_frame_captures | 5 |
| extract_transcript_concepts (incl. reduce) | 11 |
| everything else | ~2 |
| **total** | **~112** |

So a full pass is about two hours, and two stages—speaker correction and section
headings—are 58% of it. Any rerun that repeats those two has repeated most of the cost.

### What is verified and what is not

Verified in a browser on the full recording, on code before today's fixes: timeline rows
wrap, concepts group into 13 themes, per-theme graphs draw with no chip stuck at x=0,
the outline groups into 24 runs headed by the time each begins, 168 frames render with
none broken, the Concepts panel is 865 px rather than 18,623.

Verified on a fresh workspace with a short source, on the current code: an unchanged
rerun is 5 s with zero API calls; a `--segments` rerun does not repeat Deepgram or
speaker correction.

**Not verified:** any of today's fixes on the full recording. Hint exclusion was inert
until this afternoon—no analysis stage received the hints—so the concept map, outline
and synopsis have never been produced with a teaser actually excluded at scale. The
frame floor, the reduce carrying instructions, and outward span rounding are likewise
unrun at scale. A run is in flight as this is written.

### What the docs claim that is false

`docs.md` line 162: "Mark or unmark a segment in the hints file → reuses the cached
transcript and everything through section headings." Measured on a fresh workspace: a
hint change re-runs `break_into_paragraphs` and `insert_section_headings`—46 minutes on
#501. The cause is a real design tension, not a bug: hints are written back to the
stored resource so they stick to the item across runs, and the stored resource is what
kash hashes. Recorded transcribe inputs show it directly:
`watch_1.resource.yml@sha1:6b7b99fa` on a plain run, `@sha1:86b7c1d8` with hints,
transcript bodies byte-identical.

`docs.md` line 62: "12 hours or more is supported." No recording longer than 5 h 15 m
has ever been run. The design has no ceiling that would stop it; that is an argument,
not a measurement.

### How this branch has failed, six times

Every serious defect on this branch had the same shape: a helper was written and
unit-tested, and the wired path was never run. `--segments` failed on line one of every
invocation. Hints never reached the analysis. A cache fix landed inside a branch that
never executes for YouTube URLs. The frame cap was calibrated against a 22-minute
example that does not exist. Each passed its tests. The discipline that caught them, and
that this plan requires for every task below: **run the CLI end to end on the short
source before committing, and check the new test fails with the fix reverted.**

## Design

### Approach

Prove, then make the docs true, then close the design gap. In that order, because the
docs cannot be made true until the measurement exists, and the design gap (sticky hints
versus cache identity) has two defensible answers that the user should choose between.

### Components

- `transcribe_commands.py`: pipeline order, the late-input boundary, persistence.
- `transcription_metadata.py`: what is stored on the resource and therefore hashed.
- `chunking.py`, `concept_map.py`, `transcript_overview.py`: the analysis stages that
  now receive hints.
- `frame_density.py`: the thinning floor.
- `docs.md`: the rerun table and the scale claim.

### API Changes

None new. `--segments none` / `--instructions none` (review R6) is landing separately.

## Implementation Plan

### Phase 1: Prove it, and make every claim true

- [ ] Full-scale run of the current code on #501, plain then `--segments`, and browser
  verification of the result: frame count, theme count, outline groups, teaser
  collapsed, no broken frames, no traceback. Record the per-stage times. (dt-qc7j child,
  new)
- [ ] Rewrite `docs.md` row 162 to what is measured: a hint change reuses the transcript
  and speaker correction and repeats paragraph formatting and section headings, about 45
  minutes on a five-hour recording. Honest now; Phase 2 makes it cheap. (new)
- [ ] Reword the 12-hour claim to "tested end to end at five hours; the design has no
  ceiling below that scale" until a longer run exists. (dt-qc7j)
- [ ] Land the five outstanding review fixes—R6, R8, R9, R10, R11—and post the
  disposition map on PR #19. (dt-348i)
- [ ] Preflight free disk space before download and before frame capture, with a clear
  message. A run died last night when the boot volume filled. (dt-bier)
- [ ] Report a stage failure as one line naming the stage and the cause, not a
  traceback. A two-hour run that ends in a stack dump is not clean. (dt-ljkg)
- [ ] Confirm and close the two segment beads the work already covers: views respect
  exclusions (dt-hesk, the collapse) and the detection pass (dt-88st,
  `_suggest_segments`), or record what is still missing.

### Phase 2: Make a hint edit cheap

- [ ] Decide the stickiness question (see Open Questions) and implement the chosen
  option so a `--segments` rerun resumes at the outline. Then restore row 162 to its
  original wording, now true. (dt-xjlp)

### Phase 3: Twelve hours

- [ ] One real run on a 12-hour source, cost stated up front, per-stage times recorded,
  the page verified. Only then does the 12-hour claim return to the docs. (dt-qc7j)

## Testing Strategy

The full-scale run is the test. Supporting it: the fresh-workspace three-pass script
(plain, plain again, `--segments`) on the 3-minute SNL source, which runs in under three
minutes and would have caught every one of the six defects above on the day it was
written. Every task in Phase 1 runs it before committing. Every new test is checked
against the reverted fix.

## Rollout Plan

Merges to `main` as PR #19 once Phase 1 is complete and the disposition map is posted.
Phase 2 and 3 are follow-on PRs.

## Open Questions

- **Stickiness.** Hints and instructions are written back to the stored resource so a
  later run without the flag still honours them. That is what makes a hint change re-run
  46 minutes of formatting. Two ways out: (a) keep stickiness and store the late inputs
  in a sidecar the hash does not cover—more plumbing, preserves the feature; (b) drop
  stickiness and require `--segments` on every run—one flag, simplest code, removes the
  need for a "clear" affordance at all. This is a product choice.
- **Twelve hours.** A real validation costs roughly five hours of wall time and the
  Deepgram request for a 12-hour file. Worth doing once, or leave the claim softened?

## References

- `plan-2026-09-04-chunked-extraction.md`, `plan-2026-09-04-transcript-segments.md`
- PR #19 and its review: https://github.com/jlevy/deep-transcribe/pull/19
- Measurements are recorded on the beads linked to this spec.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
