---
title: Chunked Extraction for Long Recordings
description: Run the whole-document extraction stages over time-based chunks snapped to section boundaries, then stitch the results, so analysis scales with the length of the recording instead of being capped by one model call.
author: Joshua Levy with Claude assistance
---
# Feature: Chunked Extraction for Long Recordings

**Date:** 2026-09-04

**Author:** Joshua Levy with Claude assistance

**Status:** Draft

## Overview

Three stages send the entire transcript to a model in a single call: the concept map,
the outline, and the synopsis.
That works for a short talk and fails in two different ways on a long one.

The first failure is a ceiling.
Measured on a 5.3-hour podcast, the transcript runs 55,122 words, about 74k tokens, at
roughly 10,500 words per hour.
A twelve-hour recording is about 170k tokens, which fits a 200k-context model only
barely once the prompt and the response are counted, and fourteen hours does not fit at
all.

The second failure arrives long before the ceiling and matters more: **the analysis does
not grow with the material.** Concept extraction is capped at 24 concepts.
That is a reasonable map of a four-minute sketch and a poor one of a five-hour
conversation covering programming with AI agents, open source, Linux, fatherhood,
politics, and mortality.
The cap was set for legibility, but applying one budget to every length means a long
recording gets a thinner analysis than a short one, per hour of content.

The fix is to stop treating the recording as one unit.
Extraction runs over chunks of the timeline, and the results are stitched together.

## Goals

- Analysis that scales with the length of the recording rather than a fixed budget.
- No whole-document model call in any stage, removing the context ceiling entirely.
- Chunks that are semantically coherent, so extraction sees whole topics.
- A modest number of calls: roughly one per half hour to hour of audio, not one per
  section.
- Stitched output that reads as one analysis, with no duplicate concepts and no dangling
  relations.

## Non-Goals

- Chunking the transcript itself, or the speech-to-text request, both of which stay
  whole.
- Re-chunking work that already windows correctly, such as speaker correction and
  section headings.
- Per-section extraction, which would mean hundreds of calls on a long recording.

## Design

### Chunks are time-based and snapped to sections

A chunk targets a duration — about half an hour to an hour of audio — and its boundaries
move to the nearest section boundary.

Time sets the budget, so the number of calls is predictable and proportional to length:
about 5 to 10 for this five-hour episode, about 12 to 24 for twelve hours.
Sections set the actual cut, so no chunk begins or ends mid-topic; the sectioning pass
has already found where topics change, and its boundaries are the natural seams.

A section longer than the target duration is a chunk on its own rather than being split,
since splitting a topic is the thing this design exists to avoid.

### Budgets become per-chunk

`MAX_CONCEPTS` stops being a property of the recording and becomes a property of a chunk
— on the order of eight to twelve.
A five-hour episode then yields roughly 50 to 70 concepts and a twelve-hour one roughly
120 to 170, which is what “a map of this conversation” should mean at those lengths,
while a short talk is unchanged because it is a single chunk.

### Stitching

Extraction returns per-chunk results that have to become one analysis.

**Concepts merge by identity.** The same concept legitimately appears in several chunks:
a five-hour conversation returns to AI agents repeatedly.
Merging is by normalized id, falling back to a normalized label, and a merged concept
takes the union of its mentions, the union of its speakers, the span from earliest to
latest mention, and the first non-empty gloss.

**Relations resolve after the union, not before.** A chunk can name a relation to a
concept it never saw, and that target may exist in another chunk.
Resolution therefore runs once over the merged set, and only then are unresolvable
relations dropped — the same validation the index already performs, moved after the
merge rather than before it.

**The outline is already sectional**, so per-chunk outlines concatenate in timeline
order with no reconciliation needed.

**The synopsis reduces.** Per-chunk summaries are written first, then a final pass
summarizes those summaries into the two-paragraph synopsis.
The reduce step reads a few thousand words rather than the whole transcript, so it stays
within budget at any length.

### The reduce pass works on structure, not text

The reason this scales is that everything after extraction is small.

A five-hour transcript is 55,000 words, but its *outline* is a couple of thousand, and
50 to 70 concepts with their glosses are about the same.
Whatever the recording’s length, the reduce pass reads an amount of material closer to a
long article than to a book — and a twelve-hour recording changes that by a factor of
two, not by a factor that breaks anything.

That headroom is what turns the reduce pass from plumbing into the step that makes the
analysis coherent. Working from the extracted structure, it can afford to actually
organize:

- **Merge what is the same.** Chunk boundaries produce near-duplicates that exact
  identity matching misses — “AI coding agents” in one chunk and “agentic coding” in the
  next. A pass that can see all the labels at once can collapse them; a merge keyed only
  on identity cannot.
- **Group into themes.** With fifty or more concepts, a flat list stops being a map.
  The reduce pass can impose a second level — a handful of themes, each holding its
  concepts — which is exactly the hierarchy the timeline spec left as an open question
  for long recordings.
- **Order and prune.** It can put the outline in a sensible progression rather than raw
  chunk order, and drop concepts that turned out to be minor once the whole conversation
  is in view — a judgment no single chunk could make.

So the pipeline is: extract locally where the detail is, organize globally where the
overview is. Neither step ever sees more than it can handle, and the global step is the
one that decides what the analysis actually says.

### Ordering and determinism

Chunks are processed in timeline order and merged in that order, so a rerun produces the
same analysis. Concept ids stay stable because they derive from labels, and the merge is
order-independent for everything except which gloss wins, which the timeline order
fixes.

## Implementation Plan

### Phase 1: Chunking and concepts

- [ ] Add chunk planning: group sections into chunks targeting a configurable duration,
  snapping to section boundaries, with an over-long section becoming its own chunk.
- [ ] Make the concept budget per-chunk and run extraction per chunk.
- [ ] Add the merge: union mentions and speakers by concept identity, recompute spans,
  and resolve relations once over the merged set.
- [ ] Verify on the long-form fixture that concept count scales with duration and that
  no duplicates or dangling relations survive.

### Phase 2: Outline and synopsis

- [ ] Generate the outline per chunk and concatenate in timeline order.
- [ ] Generate per-chunk summaries and reduce them into the final synopsis.
- [ ] Extend the reduce pass beyond merging: collapse near-duplicate concepts that
  identity matching misses, group concepts into themes once there are enough to need it,
  and order the outline as a progression rather than in raw chunk order.
- [ ] Confirm no stage sends the whole document, and that a fourteen-hour transcript,
  which cannot fit one call, completes.

## Open Questions

- What is the right target chunk duration?
  Half an hour gives a finer analysis at roughly double the calls; an hour is cheaper
  and may still be plenty.
  Worth trying both against the same episode and comparing the concept maps.
- Should the per-chunk concept budget scale with the chunk’s own word count rather than
  being fixed, so a dense chunk yields more than a sparse one?
- With many more concepts, does the concept graph stay legible, or does it need the
  two-level theme hierarchy already noted as an open question in the timeline spec?

## References

- `docs/project/specs/active/plan-2026-09-04-transcript-segments.md` — the sectioning
  pass whose boundaries this chunks on
- `src/deep_transcribe/concept_map.py` — `MAX_CONCEPTS` and the extraction to be chunked
- `src/deep_transcribe/transcript_overview.py` — the outline and synopsis stages

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
