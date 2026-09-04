---
title: Segment Detection and Reusable Exclusion Slices
description: A detection pass that proposes non-content spans as reviewable slices, and a rendering pass that truncates them on boundaries without touching the canonical transcript.
author: Joshua Levy with Claude assistance
---
# Feature: Segment Detection and Reusable Exclusion Slices

**Date:** 2026-09-04

**Author:** Joshua Levy with Claude assistance

**Status:** Draft

## Overview

Long-form podcasts carry material that is real speech but not the conversation: sponsor
reads, an intro monologue that previews and duplicates the interview, and an outro.
Left in, sponsor brands become extracted entities, the intro’s preview competes with the
actual discussion in the concept map and outline, and the timeline gives advertising the
same weight as content.

The design keeps the expensive artifact whole and makes the editing an overlay.
Transcription always covers the entire source, so its cache stays canonical and
complete. A separate detection pass proposes spans to exclude and writes them out as
timestamp ranges.
Those ranges are an ordinary reviewable file that can be edited by hand
and supplied back to a later run, which truncates the content inside them.

That separation matters: detection is a judgment call, so it should produce a proposal a
person can read and correct, not a silent deletion inside a pipeline stage.

## Goals

- Detect non-conversation spans (sponsor, intro, outro, and duplicated preview material)
  and classify each with a reason and a confidence.
- Write the proposal as timestamp ranges in the slice format kash already understands,
  as a file a person can review, edit, and keep.
- Accept that file on a later run and apply it, with transcription reusing its cache
  untouched.
- Truncate on natural boundaries, never mid-sentence: resolve each boundary by seeking
  both directions to the nearest paragraph break, falling back to a sentence break, so
  excluded regions are whole runs of paragraphs and the surviving text still reads
  cleanly.
- Keep every downstream view consistent with the exclusions: concepts, outline,
  synopsis, speaker statistics, and the timeline.
- Make what was removed visible rather than silent, with the excluded time reported.

## Non-Goals

- Editing the media itself, or re-transcribing a trimmed source.
- Deleting anything from the canonical transcript document.
- Fully automatic removal with no reviewable artifact.
- Detecting speech that is merely off-topic; this targets structurally separate
  material, not digressions.

## Design

### The exclusion file

Detection writes a small file next to the workspace outputs, listing ranges in kash’s
existing `Slice` vocabulary (`HH:MM:SS-HH:MM:SS` or seconds), one per line with its
classification, confidence, and a short quote for orientation:

```yaml
exclusions:
  - slice: 00:00:00-00:04:12
    kind: intro
    confidence: high
    note: Host monologue previewing the conversation.
    opening: "The following is a conversation with David…"
  - slice: 00:04:12-00:06:30
    kind: sponsor
    confidence: high
    note: Reads for two sponsors.
    opening: "This episode is brought to you by…"
```

`kind` is a closed set: `intro`, `sponsor`, `outro`, `duplicate`. The file is the
contract between the two runs, and it is meant to be edited: a person can delete a range
they disagree with, adjust a boundary, or add one detection missed.

### Two passes, one cache

**Pass one — detect.** A `detect_segments` stage reads the full transcript and proposes
ranges, citing citation keys the way concept mentions do, so a proposal can always be
traced to real timestamps.
It writes the exclusion file and changes nothing else.

**Pass two — apply.** A later run given `--exclusions FILE` truncates the content inside
those ranges. Because transcription is unchanged and content-addressed, this run reuses
the raw transcription cache and starts at the formatting boundary — the same property
the processing-instructions work already relies on.

### Boundary snapping

A range from detection is approximate, so each boundary is resolved against the
document’s real structure before anything is excluded.

The unit of exclusion is the paragraph.
Sponsor reads and intros begin and end at paragraph breaks in practice, and paragraphs
are what the timestamps already anchor, so an excluded region should be a whole run of
paragraphs rather than an arbitrary time window.

For each proposed boundary the search seeks **both directions** from that time, rather
than being forced one way, and takes the nearest candidate by this preference:

1. a paragraph break,
2. failing that, a sentence break,
3. failing that, a citation timestamp.

A paragraph break within tolerance always wins over a nearer sentence break, since
landing on the stronger boundary matters more than landing on the closest one.
When two candidates of the same strength are equally near, the tie goes to the one that
excludes less — the later start, the earlier end — so a snap can never eat into
surviving speech.

This is the same bidirectional token seeking `backfill_timestamps` already uses to
resolve timestamps (`search_tokens(...).at(offset).seek_back(...)` and its forward
counterpart), applied to boundary resolution instead.

If snapping would invert a range or leave it empty, the range is dropped with a warning
rather than guessed at.

### Downstream consistency

Excluded units are marked in the transcript index rather than deleted, so every view can
agree without the document losing text:

- Concept extraction and the outline read only included units.
- Speaker statistics report content time, with excluded time shown separately.
- The Timeline overview shades excluded spans distinctly, so their share is visible at a
  glance.
- The transcript marks excluded passages rather than removing them, since the words were
  really said; `--elements` may later offer an export that omits them entirely.

## Implementation Plan

### Phase 1: Detection and the exclusion file

- [ ] Add the exclusion file schema and a reader/writer using kash’s `Slice`.
- [ ] Add the `detect_segments` LLM stage with the closed `kind` vocabulary, citing
  citation keys, and validation that drops unresolvable proposals.
- [ ] Add `--detect-segments` to write the file, reporting what it found and the total
  time proposed for exclusion.

### Phase 2: Applying exclusions

- [ ] Add `--exclusions FILE`, validated and boundary-snapped before use.
- [ ] Mark excluded units in the transcript index; confirm the raw transcription cache
  is reused on the second run.
- [ ] Make concepts, outline, synopsis, statistics, and the timeline respect the marks;
  show excluded time rather than hiding it.
- [ ] Extend the runbook: detect, review the file by hand, rerun, and verify the cache
  was reused and no sentence was cut.

## Open Questions

- Should detection run inside `--deep` by default and simply report, leaving application
  explicitly opt-in? Reporting is cheap and the proposal is harmless until applied.
- Is `duplicate` reliably separable from a host legitimately restating a point later in
  the conversation? It may need a higher confidence bar than the structural kinds.
- Should the exclusion file live in the workspace or beside the media, given it is
  really a property of the source rather than of one run?

## References

- `docs/project/specs/active/plan-2026-09-03-dt-design-system-refactor.md` — the view
  the exclusions feed
- `kash.utils.common.url_slice` — the `Slice` type and parsing this reuses
- `src/deep_transcribe/concept_map.py` — the citation-validation pattern detection
  should follow

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
