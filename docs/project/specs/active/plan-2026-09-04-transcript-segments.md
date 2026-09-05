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

**A preview clip leaves a measurable trace, which is evidence rather than proof.** The
`Episode highlight` chapter was compared against the rest of the conversation: 14 of its
15 substantive sentences are near-verbatim repeats of later material, drawn from seven
separate points spread across the five hours — 0:04, 0:38, 0:41, 2:03, 2:44, 3:12, and
4:23.

The similarity was high here (0.97–1.00) because a teaser reuses the same audio, so
speech-to-text produces nearly the same words.
But speech-to-text is not deterministic in the way exact matching would need: the same
audio can transcribe differently under different surrounding context, and a teaser that
was re-edited, re-recorded, or laid under music will diverge further.
So similarity is a strong signal to be thresholded loosely, never an equality test.

What makes it dependable is applying it **per section rather than per sentence**. Asking
whether a whole section substantially repeats material appearing later is a judgment a
model makes well, and a fuzzy-match score over that section is exactly the evidence it
needs to make it.
Neither alone is trustworthy; together they are, and the failure mode a
model would face on its own — mistaking a host restating a theme for a teaser — is
precisely what the similarity evidence rules out.

Intro material is different again: it is original speech in a recognizable register
(`The following is a conversation with…`), so it is classified rather than matched.
Promotional breaks — sponsor reads, but equally a plug to subscribe or buy a book — are
the case with no metadata and no duplication to lean on, and are the one kind that
genuinely needs a model reading for a change in register.

**A transition usually leaves a gap, and the timestamps can see it.** Segments are
normally separated by something other than speech — a music string, a beat of silence, an
edit point — and that shows up as time between one sentence ending and the next
beginning.

Measured here, the teaser-to-intro boundary at 1:27 carries roughly a 17-second gap,
consistent with a musical transition, and it is one of the largest anywhere in the
episode.

The caveat is that gaps alone would produce false positives: comparable gaps appear
mid-conversation, where a speaker simply pauses, laughs, or thinks.
Gap size is corroboration for a boundary that other evidence already suggests, not a
detector on its own.

It is also more approximate than it needs to be.
The pipeline keeps a timestamp for each sentence’s *start*, so a gap has to be inferred
by estimating how long the previous sentence took to say.
Speech-to-text returns per-word timings including where each word ends, which would make
these gaps exact rather than estimated — that data is currently discarded.

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
| `preview` | fuzzy similarity against later text as evidence, judged per section |  |
| `intro` | **yes** | host framing before the conversation starts |
| `promo` | **yes** | an advertising or promotional break: a sponsor read, but equally a plug to subscribe, buy a book, or join something |
| `outro` | **yes** | closing remarks, credits, appeals |

`source` records how the segment was determined — `chapter` or `detected` — so a reader
can see which boundaries came from the publisher and which from inference.
`suppressed` is a default implied by `purpose` and may be overridden per segment.

### Building segments: one windowed pass, then a cheap classification

Segments are not a new detection problem.
The pipeline already inserts section headings with a windowed pass over the transcript,
and a section boundary is exactly what a segment boundary is.
So the work is to make that existing pass aware that a promotional break deserves its
own section, then walk the resulting headings and label each one.

**Pass one — sectioning (extended, not new).** `insert_section_headings` runs
`LLM.default_fast` over `WINDOW_128_PARA` with the `adds_headings` diff filter, which
accepts only insertions inside heading tags.
That filter is the reason this is safe to extend: whatever the prompt asks for, the
model cannot alter a word of the transcript — the worst case is a heading in an odd
place.

The prompt gains one requirement: when the speaker breaks from the conversation into an
advertising or promotional read, that break starts its own section and the conversation
resumes with another after it.
A promo absorbed into a surrounding topical section cannot be suppressed cleanly later,
so the boundary has to exist before anything can be labeled.

**Pass two — classification (small and cheap).** The result is a list of headings, not
five hours of text.
For this episode that is on the order of tens of entries, so a single
call can read the heading list with a little context under each — the opening sentence
and its timestamp — and assign a purpose to every one.
Scoring a short labeled list is a far easier task than finding structure in a
transcript, and a wrong answer is a mislabeled section rather than a missing one.

**Chapters, where they exist, are evidence for pass two rather than a separate path.** A
chapter titled `Episode highlight` or `Introduction` is a strong prior for the section
that covers it, and chapter boundaries can be offered to pass one as suggested split
points. Chapters never mark promos, so they cannot replace either pass.

**Scale.** The 5.3-hour episode is about 1,263 paragraphs, so roughly 10 windows on the
fast model; twelve hours is roughly 23. Classification stays one call regardless of
length. Both scale linearly and cheaply, which is the point of reusing the windowed pass
rather than asking one model to read everything.

**The known weakness is the window seam.** `WINDOW_128_PARA` shifts by its full size
with no overlap, so a promo straddling a boundary is seen as two partial fragments,
neither obviously a promo.
Options, in order of preference: give the sectioning window a small overlap; or let pass
two merge adjacent sections it labels the same way, which repairs a split promo without
touching the windowing.

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

- [ ] Add near-duplicate preview detection: match early text against later text and mark
  a leading run of verbatim repeats as `preview`. No model call needed.
- [ ] Add the model pass for the kinds that need it — sponsor interjections, intro and
  outro register — citing citation keys and dropping what does not resolve.
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
