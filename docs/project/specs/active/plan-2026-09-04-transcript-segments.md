---
title: Transcript Segments and Default Suppression
description: A first-class segment structure over the timeline that states each part's purpose and whether it is suppressed by default, built from chapters where they exist and from the transcript where they do not.
author: Joshua Levy with Claude assistance
---
# Feature: Transcript Segments and Default Suppression

**Date:** 2026-09-04

**Author:** Joshua Levy with Claude assistance

**Status:** Draft

## Overview

A long podcast is not one undifferentiated conversation.
It opens with a highlight clip that replays material from later, then a host monologue,
then the interview, sometimes with sponsor reads dropped in, and an outro at the end.
Treated as one flat transcript, the analysis suffers: a teaser duplicates the real
discussion in the concept map and outline, sponsor brands become extracted entities, and
the timeline gives advertising the same weight as content.

This adds **segments** as a first-class part of the transcript: a labeled partition of
the timeline where each segment states what it is for and whether it is suppressed by
default.
Segments are extracted into the output as their own section, and suppressed ones
are folded away in the transcript rather than deleted.

## What the evidence actually supports

Before designing detection, three sources were measured against a real 5.3-hour episode
(Lex Fridman #501). The results ruled out the obvious approaches.

**YouTube chapters are reliable, and incomplete.** The episode carries 23 chapters with
exact boundaries and human-written titles, including `Episode highlight` (0:00–1:27) and
`Introduction` (1:27–2:56). That is an excellent skeleton — better than anything
inferred, and free.
But **no chapter marks a sponsor**, and no chapter title contains any
sponsor name.

**The description names sponsors but does not locate them.** The description lists
eight: Wispr Flow, Blitzy, NetSuite, Shopify, LMNT, Plaud, Higgsfield AI, Perplexity.
None of those names appears in any chapter title.

**Matching sponsor names against the transcript produces false positives, not
locations.** Five of the eight never appear in the transcript at all.
The three that do appear are ordinary conversation: the guest discussing Shopify’s
layoffs and its CTO, and naming Perplexity and Plaud as products under discussion.
Searching the full transcript for ad-read phrasing (`brought to you by`,
`this episode is sponsored`, `use code`) returns **zero matches**.

The conclusion is that this episode has no in-audio sponsor reads at all, despite naming
eight sponsors in its description.
So description metadata cannot be treated as evidence that an ad exists in the audio,
and name matching would have suppressed real conversation.

**Therefore the transcript is the ground truth and metadata is only a hint.** When a
segment changes character — a monologue becomes an interview, an interview breaks for a
read — it is obvious in the text.
That is what a model reading the transcript is good at, provided it is given the
structure to fill in rather than asked to find everything from scratch.

## Design

### The segment structure

Segments partition the timeline.
Every second of the recording belongs to exactly one, so nothing is silently unaccounted
for.

```yaml
segments:
  - span: 00:00:00-00:01:27
    title: Episode highlight
    purpose: preview
    suppressed: true
    source: chapter
    note: Teaser assembled from later in the conversation.
  - span: 00:01:27-00:02:56
    title: Introduction
    purpose: intro
    suppressed: true
    source: chapter
  - span: 00:02:56-00:18:14
    title: Programming with AI agents
    purpose: content
    suppressed: false
    source: chapter
```

`purpose` is a closed set:

| purpose | suppressed by default | what it is |
| --- | --- | --- |
| `content` | no | the conversation itself |
| `preview` | **yes** | a highlight or teaser replaying material from later |
| `intro` | **yes** | host framing before the conversation starts |
| `sponsor` | **yes** | an advertising or promotional read |
| `outro` | **yes** | closing remarks, credits, appeals |

`source` records how the segment was determined — `chapter` or `detected` — so a reader
can see which boundaries came from the publisher and which from inference.
`suppressed` is a default implied by `purpose` and may be overridden per segment.

### Building segments

**Chapters first, when they exist.** Chapters give exact boundaries and human titles for
free, and yt-dlp already returns them.
They become the initial partition, and each is classified by purpose.

**Detection fills the gaps.** Sponsor reads and similar interjections are usually not
chaptered, so the model reads the transcript and proposes segments that split an
existing one. This is a much smaller and better-grounded task than scanning five hours
cold: for each candidate it cites citation keys, exactly as concept mentions do, and
anything that does not resolve is dropped.

**Without chapters, detection produces the whole partition.** The same classification
runs over the transcript alone, which is the general case for local recordings and
sources without chapter metadata.

Because the model is asked to *classify a labeled structure* rather than *find
everything*, the prompt can be short, specific, and cheap — and a wrong answer is a
mislabeled segment rather than a missing one.

### Boundary snapping

Detected boundaries are approximate, so each is resolved against the document’s real
structure before anything is suppressed.

The unit is the paragraph.
For each proposed boundary the search seeks **both directions** and takes the nearest
candidate by strength: a paragraph break, else a sentence break, else a citation
timestamp. A paragraph break within tolerance beats a nearer sentence break, since
landing on the stronger boundary matters more than landing on the closest one.
Ties of equal strength go to the option that suppresses less — the later start, the
earlier end — so a snap never eats into surviving speech.
This reuses the bidirectional token seeking `backfill_timestamps` already relies on.

Chapter boundaries are snapped the same way, since a publisher’s timestamps are also
approximate.

### In the output

**A Segments section** lists the partition: each segment’s title, purpose chip, span,
and duration, with suppressed ones visibly marked.
Reading it answers “what is actually in this recording, and how much of it is the
conversation.”

**In the transcript**, a suppressed segment collapses to a single line carrying its
purpose chip, title, and duration — the same chip vocabulary the concept views use.
Clicking expands it in place in the supporting gray, so a reader can always drill in but
is not made to scroll through a teaser to reach the interview.

**In the analysis**, suppressed segments are absent: the synopsis, outline, concepts,
and claims read only unsuppressed units.

**In the statistics**, speaker figures report conversation time, with suppressed time
shown separately — how much of an episode is teaser and advertising is itself worth
knowing.

**On the timeline**, suppressed spans are shaded distinctly rather than dropped, so
their position and share stay visible and the axis still matches the source.

**In print**, a suppressed segment prints as its collapsed line only.

### Reuse across runs

The segment list is written as an ordinary file that can be reviewed, hand-corrected,
and supplied to a later run.
Transcription always covers the whole recording, so its cache stays canonical and a
rerun that changes suppression starts at the formatting boundary rather than
re-transcribing.

## Goals

- Partition every recording into labeled segments covering the full timeline.
- Use publisher chapters where they exist, and detection where they do not.
- Suppress preview, intro, sponsor, and outro material by default, keeping content.
- Never delete text: suppressed passages stay in the document, collapsed and grayed.
- Keep every view consistent, and report suppressed time rather than hiding it.
- Snap boundaries to paragraphs so no sentence is ever cut.
- Write segments as a reviewable, editable, reusable file.

## Non-Goals

- Editing the media, or re-transcribing a trimmed source.
- Treating description metadata as proof that an ad exists in the audio; measurement
  showed it is not.
- Matching sponsor names against the transcript, which produced only false positives.
- Detecting merely off-topic talk; this targets structurally distinct material.

## Implementation Plan

### Phase 1: Segments from chapters

- [ ] Fetch and store chapter data (yt-dlp already returns `chapters`).
- [ ] Add the segment structure to the transcript index, covering the whole timeline.
- [ ] Classify each chapter’s purpose, defaulting suppression from it.
- [ ] Render the Segments section and the collapsed transcript treatment.

### Phase 2: Detection where chapters do not reach

- [ ] Add the detection pass for unchaptered interjections and for sources with no
  chapters at all, citing citation keys and dropping what does not resolve.
- [ ] Snap all boundaries, chapter and detected alike.
- [ ] Write and read the reviewable segment file; confirm a rerun reuses the
  transcription cache.
- [ ] Make concepts, outline, synopsis, statistics, and the timeline respect
  suppression.

## Open Questions

- Should chapter titles also replace LLM-invented section headings?
  They are human-written and free, and the current `insert_section_headings` stage pays
  a model to guess at what the publisher already stated.
- How should a segment that is partly promotional be handled — split, or labeled by its
  dominant purpose?
- Is `preview` reliably distinguishable from a host legitimately restating a theme?
  The measured case was unambiguous because the chapter said `Episode highlight`.

## References

- `docs/project/specs/active/plan-2026-09-03-dt-design-system-refactor.md` — the views
  segments feed
- `src/deep_transcribe/concept_map.py` — the citation-validation pattern detection
  follows
- `kash.utils.common.url_slice` — the `Slice` type spans reuse

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
