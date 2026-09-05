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

**Verified on the full recording with the current code** (export of 16:58, commit
7eeb87d): 11 timeline rows, 173 frames with none broken, 13 themes holding 124 concepts,
13 per-theme graphs with no chip at x=0, 27 outline groups, 0 warnings in a 96-minute
run. Hint exclusion holds at scale: 0 of 681 concept mentions and 1 of 185 outline chips
fall inside the hinted teaser, the one leak being the paragraph the pre-R7 rounded span
misses. A same-hints rerun took 13 s. Two defects came out of the evidence and are
tracked: the collapse renders one span as four per-section fragments (dt-4hwa), and
thinning keeps about 170 of a 237 target on real spacing (dt-k1cf).

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

- [x] Full-scale run of the current code on #501, plain then `--segments`, and browser
  verification of the result: frame count, theme count, outline groups, teaser
  collapsed, no broken frames, no traceback. Record the per-stage times. (dt-qc7j child,
  new)
- [x] Rewrite `docs.md` row 162 to what is measured: a hint change reuses the transcript
  and speaker correction and repeats paragraph formatting and section headings, about 45
  minutes on a five-hour recording. Honest now; Phase 2 makes it cheap. (new)
- [x] Reword the 12-hour claim to "tested end to end at five hours; the design has no
  ceiling below that scale" until a longer run exists. (dt-qc7j)
- [x] Land the five outstanding review fixes—R6, R8, R9, R10, R11—and post the
  disposition map on PR #19. (dt-348i)
- [x] Preflight free disk space before download and before frame capture, with a clear
  message. A run died last night when the boot volume filled. (dt-bier)
- [x] Report a stage failure as one line naming the stage and the cause, not a
  traceback. A two-hour run that ends in a stack dump is not clean. (dt-ljkg)
- [x] Confirm and close the two segment beads the work already covers: views respect
  exclusions (dt-hesk, the collapse) and the detection pass (dt-88st,
  `_suggest_segments`), or record what is still missing.

### Phase 2: Make a hint edit cheap

- [x] Done without a design change. The cost was never stickiness: kash fills
  `original_filename`, `history` and `modified_at` on load and not on a fresh item, so
  the first re-persist of a resource changed its hashed bytes once.
  `persist_item_metadata` now writes all three from the start; a hint change resumes at
  the outline whether or not the source had hints before. (dt-xjlp)

### Phase 3: Twelve hours, by envelope

The owner ruled out a real twelve-hour run: five hours proven end to end plus arithmetic
showing every duration-scaling constraint clears at twelve is the bar. Ratio used: 12 h
over the measured 5.26 h, or 2.28.

| constraint | measured at 5.26 h | at 12 h | limit | clears |
| --- | --- | --- | --- | --- |
| media download on the workspace volume | 4.0 GB | ~9 GB | preflight checks free space (dt-bier) | yes |
| 16 kHz mp3 sent to Deepgram | 54 MB | ~120 MB | 2 GB request cap | yes |
| Deepgram processing time | 52 s | ~120 s | 600 s cap | yes |
| client request budget | scales with duration | ~120 s needed | 7,200 s ceiling | yes |
| speaker correction | 32 min, windowed | ~73 min | no single call grows | yes |
| paragraph formatting | 11 min, `WINDOW_2K_WORDTOKS` | ~25 min | windowed | yes |
| section headings | 32 min, `WINDOW_128_PARA` | ~73 min | windowed | yes |
| outline and synopsis | 7 min, chunked | ~16 min | reduce reads summaries only | yes |
| frame capture | 1,442 captured, 173 kept, 3 min | ~3,300 captured, ~390 kept, ~7 min | thinning target 45/h | yes |
| concept extraction and reduce | 9 min, chunked; 125 concepts | ~21 min; ~285 concepts | batches of 25, ~12 batches | yes |
| page | 181,000 px, 11 timeline rows | ~410,000 px, ~25 rows | panels collapse by theme | yes |
| wall time, transcript cached | 96 min | ~3.7 h | none | — |

No stage sends the whole transcript in one model call: the three expensive stages are
windowed and the analysis stages are chunked, so every cost above is linear in duration.
The speaker-roster step reads metadata abbreviated to 4,000 characters; the synopsis
reduce reads chunk summaries; theme names are consolidated across batches in one bounded
call.

Residual risk, accepted: a windowed stage of ~73 minutes is one action, so a content
failure inside it loses that stage rather than a window. kash retries HTTP 429 and 5xx;
the cache resumes at the failed stage on rerun.

- [x] Envelope recorded; dt-qc7j closed on it.

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

- **Stickiness.** Resolved: hints stay on the resource. The expensive rerun was kash
  bookkeeping fields, fixed in `persist_item_metadata`; see dt-xjlp.
- **Twelve hours.** A real validation costs roughly five hours of wall time and the
  Deepgram request for a 12-hour file. Worth doing once, or leave the claim softened?

## References

- `plan-2026-09-04-chunked-extraction.md`, `plan-2026-09-04-transcript-segments.md`
- PR #19 and its review: https://github.com/jlevy/deep-transcribe/pull/19
- Measurements are recorded on the beads linked to this spec.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
