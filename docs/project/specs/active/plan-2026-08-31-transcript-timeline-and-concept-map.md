---
title: Transcript Timeline, Speaker Analytics, and Concept Map
description: Plan for a time-mapped analytical view of a transcript, with a sticky timeline rail, speaker statistics, frame-capture connectors, and an extracted concept map.
author: Joshua Levy with Claude assistance
---
# Feature: Transcript Timeline, Speaker Analytics, and Concept Map

**Date:** 2026-08-31

**Author:** Joshua Levy with Claude assistance

**Status:** Draft

## Overview

Turn the Deep Transcribe HTML export from a well-typeset document into a document you
can also *read analytically*: who spoke, when, for how long, about what, and how the
ideas in the conversation relate to each other over time.

The export stays one self-contained HTML file with the same typography, the same reading
experience, and the same printed PDF. What it gains is a persistent sense of place in
the media timeline, a quantitative summary of the participants, a visual link from each
captured video frame back to the moment it came from, and a map of the concepts the
conversation actually covers.

Two layers make this work.
A deterministic **transcript index**, computed in the pipeline and embedded in the page
as JSON, gives the client authoritative timings and counts.
A set of small, dependency-free **client modules** render that index as a sticky
timeline rail, an analytics panel, frame connectors, and a concept map, all synchronized
to scroll position and to the existing YouTube popover player.

## Goals

- Give every paragraph and every sentence in the transcript a resolved start and end
  time, without adding visible timestamp clutter to the prose.
- Show a sticky, always-visible rail representing the whole media duration, with a
  marker for where the reader currently is.
- Assign each speaker a stable, legible color and use it consistently across the rail,
  the speaker labels, the statistics, and the concept attribution.
- Report per-speaker word, sentence, paragraph, and turn counts, along with speaking
  time, share of words, and share of time.
- Reveal what was said at any point on the rail through hover, using the speaker color,
  the timestamp, and a short excerpt or summary.
- Connect each frame capture to its point on the timeline with a drawn connector, and
  make hovering either end highlight the other.
- Extract the key concepts of a transcript, with a one-line gloss, the moments they are
  discussed, and typed relations between them.
- Lay those concepts out against the timeline so their sequence, overlap, and clustering
  are visible at a glance.
- Optionally attach short background research to each concept, under the same evidence
  and provenance rules the speaker roster already follows.
- Keep the printed PDF byte-comparable in layout to what the pipeline produces today.

## Non-Goals

- Reader-authored annotations, highlights, or notes.
  All markers on the rail are derived by the pipeline.
  (See Open Questions for how this could be added later without redesign.)
- Any new client-side runtime dependency.
  No D3, no charting library, no bundler, no build step.
- Any change to the visible prose of the transcript.
  The index is strictly additive and binds to markup that already exists.
- A separate analysis page, a tabbed layout, or a second export artifact.
- Replacing the existing table of contents, tooltip, or YouTube popover components.
  The new modules coexist with them and reuse their conventions.
- Server-side rendering of charts, or emitting images for the visualizations.
- Editing, re-timing, or re-segmenting the transcript itself.
- Word-level timing. Sentence granularity is the floor for this feature.

## Background

### What the pipeline already produces

The final document is `md_html`: Markdown with embedded HTML. Reading the cached
workspace at `tmp/hotel-showcase/output/workspace` shows the exact shape the client has
to work with.

Each speaker turn is a Markdown paragraph beginning with a bold label, followed by its
sentences, and ending with one timestamp citation:

```html
**Hotel Receptionist:** Good morning.
Welcome to the Transnational Hotel.
What can I do for you?
<span class="citation timestamp-link" data-src="resources/watch_1.resource.yml"
      data-timestamp="9.28"><a href="https://www.youtube.com/watch?v=...&t=9.28s">00:09</a></span>
```

Three facts about that markup matter for this design.

The citation renders at the end of the paragraph but carries the paragraph’s *start*
time. `backfill_timestamps` seeks back to the preceding paragraph break before resolving
the timestamp, so `9.28` is when the turn began, not when it ended.

`backfill_timestamps` already accepts `chunk_unit` of `sentences` or `paragraphs`.
Sentence-level timings are therefore available from the existing machinery; the default
is paragraphs only because a citation after every sentence would wreck the prose.

Frame captures are inserted immediately after the citation span, inside the same
paragraph, and carry their time in the alt text:

```html
<img class="frame-capture" src="...assets/..._0000.jpg" alt="Frame at 9.28 seconds" />
```

Section headings are ordinary `h2`. The synopsis is `div.description`, the outline is
`div.transcript-outline`, and the transcript body is `div.original`. Upstream of
`strip_html`, the raw transcription carries
`<span class="speaker-label" data-speaker-id="0">` and per-sentence
`<span data-timestamp="...">`, and the workspace metadata carries
`extra.transcription.speaker_roster`.

### What is missing

The DOM alone is nearly sufficient, which is what makes this feature tractable.
Four things are not derivable from the rendered page:

1. **Media duration.** Without it the rail has no right edge and the final paragraph has
   no end time.
2. **Stable speaker identity.** Names appear as bold text.
   Color assignment needs the ordered roster, so colors stay stable across reruns and
   across sections where a speaker is absent.
3. **Authoritative counts.** The client could split on sentence enders, but the pipeline
   already tokenizes with `flexdoc`. Counting in two different places invites two
   different answers.
4. **Concepts.** Genuinely new output, requiring a new LLM stage.

### Why a JSON index rather than richer markup

Annotating every paragraph with `data-*` attributes would mean wrapping Markdown
paragraphs in explicit HTML, which changes how they render and how every downstream
regex-based action sees them.
The transcript body is deliberately kept as clean Markdown for exactly that reason.

A single embedded JSON document avoids all of it.
The index binds to the DOM through the citation timestamp string, which is already
unique per paragraph and already present.
The prose is untouched, the PDF is unaffected, and any external tool can read the same
index without parsing HTML.

## Design

### Approach

Add one deterministic pipeline stage and one optional LLM stage, then render entirely on
the client from their combined output.

```
transcribe → ... → insert_frame_captures
                        │
                        ├── extract_concepts        (optional, LLM, --concepts)
                        │
                        └── attach_transcript_index (deterministic, always when formatted)
                                    │
                                    └── render_item_as_html → one HTML file
```

`attach_transcript_index` runs last so it can see sections, frame captures, and
concepts. It appends a hidden data block to the document body and changes nothing else.

### The transcript index

Serialized into the page as:

```html
<div class="dt-data" hidden>
  <script type="application/json" id="dt-transcript-index">{ ... }</script>
</div>
```

Shape:

```json
{
  "version": 1,
  "media": {
    "url": "https://www.youtube.com/watch?v=kq9Q9-U0vrc",
    "duration": 253.4,
    "title": "Hotel Check In — SNL",
    "has_video": true
  },
  "speakers": [
    { "id": "s0", "name": "Front Desk Employee", "order": 0 },
    { "id": "s1", "name": "Mr. Adams", "order": 1 }
  ],
  "sections": [
    { "id": "sec0", "heading": "Checking In", "start": 9.28, "end": 66.86 }
  ],
  "units": [
    {
      "uid": "p0",
      "key": "9.28",
      "speaker": "s0",
      "section": "sec0",
      "start": 9.28,
      "end": 12.34,
      "words": 12,
      "sentences": 3,
      "sentence_times": [9.28, 10.6, 11.4],
      "excerpt": "Good morning. Welcome to the Transnational Hotel."
    }
  ],
  "frames": [
    { "uid": "f0", "key": "9.28", "t": 9.28, "src": "...assets/..._0000.jpg" }
  ],
  "totals": {
    "by_speaker": {
      "s0": { "turns": 14, "words": 402, "sentences": 51, "seconds": 121.3 }
    },
    "words": 780,
    "seconds": 244.1
  },
  "concepts": []
}
```

Minification is safe for this block, verified against the real toolchain.
`minify_html` shells out to `html-minifier-terser` with `--collapse-whitespace` and
`--minify-js true`; the minifier only runs terser on scripts whose type is a JavaScript
MIME type, and it does not collapse whitespace inside raw-text elements.
A test island came through with its content unchanged, including a deliberate double
space inside a string value, while an adjacent ordinary `<script>` was minified as
normal. The Phase 1 guard test pins this behavior so a toolchain upgrade cannot silently
break it.

Design notes on the contract:

- `key` is the citation timestamp exactly as it appears in `data-timestamp`, formatted
  to two decimals. It is the join key between index and DOM. `uid` is the stable fallback
  ordinal.
- `end` for a unit is the next unit’s `start`; the last unit ends at `media.duration`.
  When duration is unavailable, the last unit’s end is its start plus the mean unit
  duration, and `media.duration` is emitted as `null` so the client can mark the tail as
  estimated.
- `sentence_times` comes from running the existing `backfill_timestamps` alignment at
  sentence granularity against the upstream timestamped item, discarding the rendered
  citations and keeping only the numbers.
  This is what makes “every part of every utterance has a timestamp” true without
  changing a character of visible prose.
- Counts are computed with `flexdoc`, the same tokenizer the rest of the pipeline uses.
- `speakers[].name` comes from `extra.transcription.speaker_roster` when present,
  falling back to the distinct bold labels in document order.
  `order` drives color assignment, so colors are stable across reruns.

### Concept extraction

A new LLM action produces, per concept:

```json
{
  "id": "reservation-glitch",
  "label": "Missing reservation",
  "kind": "topic",
  "gloss": "The booking cannot be found in the system, which sets up the upgrade.",
  "mentions": [{ "t": 16.26, "key": "16.26" }, { "t": 36.03, "key": "36.03" }],
  "span": [16.26, 60.82],
  "speakers": ["s0", "s1"],
  "relations": [{ "to": "suite-upgrade", "type": "leads-to" }],
  "research": null
}
```

`kind` is one of `topic`, `entity`, `term`, `claim`, or `decision`. Relation types are a
closed set: `leads-to`, `contrasts-with`, `elaborates`, `example-of`, `depends-on`. A
closed vocabulary keeps the graph legible and keeps the renderer from having to invent a
visual language for arbitrary model output.

Every mention must cite a timestamp that exists in the index.
Mentions that do not resolve are dropped with a logged warning rather than rendered, on
the same principle the roster step already applies: the model may only assert what the
evidence supports.

Background research is a separate, optional pass, reusing the existing `--web-search`
gate. Research notes render visually distinct from transcript-derived content and always
carry their sources.
Search results are untrusted input and are never allowed to introduce a concept, only to
annotate one the transcript already established.

### Client modules

New jinja partials under `src/deep_transcribe/resources/templates/components/`,
following the pattern kash already uses for `toc_scripts.js.jinja` and
`youtube_popover_scripts.js.jinja`: each is an IIFE, included inline, no modules to
fetch and no build step.

| Module | Responsibility |
| --- | --- |
| `dt_core.js.jinja` | Parse the index, bind it to the DOM, own the time↔pixel math, dispatch events |
| `dt_rail.js.jinja` | The sticky timeline rail, its markers, hover, and click-to-seek |
| `dt_stats.js.jinja` | The speaker analytics panel |
| `dt_frames.js.jinja` | Gutter placement and connector drawing for frame captures |
| `dt_concepts.js.jinja` | Concept ribbon and concept graph |
| `dt_viz.css.jinja` | All styles, including the speaker palette and print rules |

Modules communicate through `CustomEvent` on `document` (`dt:timechange`, `dt:hover`,
`dt:select`) and read a frozen model object published by `dt_core`. No module reaches
into another’s DOM. This matches how the existing components stay independent, and it
means the rail, the stats, and the concepts can each be developed and disabled on their
own.

`dt_core` degrades to a no-op when `#dt-transcript-index` is absent, so the template
stays safe for any document that has not been through the new stage.

### The rail

A fixed-position vertical bar in the right gutter, running the height of the viewport,
where vertical position maps linearly to media time.
The left gutter is already occupied by the table of contents, and the YouTube popover
parks at `bottom: 1rem; right: 1rem`, so the rail reserves space above the popover and
narrows when `body.yt-open` is set.

Lanes, left to right:

1. **Speaker band** — a continuous stripe colored by who is speaking.
2. **Section ticks** — a mark and label at each `h2` boundary.
3. **Frame ticks** — a small mark per captured frame.
4. **Concept spans** — thin bars for each concept’s active range (Phase 2).

Over the lanes sit two indicators: a translucent window covering the time range
currently on screen, and a crisp line at the reading center.
The line is the “you are here” marker the reader tracks while scrolling.

Interactions:

- Hover a point → a tooltip with the timestamp, the speaker in their color, and the
  opening words of that turn.
- Click → scroll the document to that moment.
- Shift-click, or click a frame tick → open the YouTube popover at that time, reusing
  `openPopover` rather than reimplementing the player bridge.
- Keyboard → the rail is focusable; arrow keys step by turn, `Home`/`End` jump to the
  ends.

**Rendering at scale.** A four-minute sketch has tens of paragraphs; a two-hour podcast
has thousands. Painting one SVG rect per unit does not scale.
The rail instead quantizes to its own pixel height: for a rail of *H* pixels it computes
*H* buckets, resolves the dominant speaker per bucket, and emits one rect per contiguous
run of identical buckets.
Cost becomes a function of rail height, not transcript length.
Ticks and spans are drawn individually since they are sparse.

### Frame connectors

On viewports wide enough to afford it, frame captures move from inline blocks into a
right-hand gutter between the text column and the rail.
An SVG overlay draws a single-stroke cubic bezier from the image’s right edge to its
tick on the rail.

Connectors are drawn only for frames intersecting the viewport, tracked with
`IntersectionObserver`, so the overlay stays sparse and cheap no matter how long the
document is. Hovering an image brightens its connector and highlights its rail tick;
hovering the tick outlines the image.

Below the gutter breakpoint, and in print, frame captures stay exactly where they are
today and no connectors are drawn.

### Speaker colors

A curated palette of eight hues with a light and a dark variant each, assigned by roster
order and cycling beyond eight.
Curated rather than hash-derived: hashing produces clashing, muddy, and occasionally
illegible colors, and reassigns them whenever a name changes.

Each color is published as a CSS custom property (`--dt-speaker-0-fg`,
`--dt-speaker-0-bg`) so the rail, the bold speaker labels, the stats bars, and the
concept attribution all read from one source.
Every foreground variant must clear WCAG AA against both `--color-bg` values.
Color is never the only channel: the stats table names every speaker in text, and rail
tooltips always state the name.

### The analytics panel

Placed between the outline and the transcript, matching the visual weight of the
existing `div.transcript-outline`.

A real `<table>` of per-speaker turns, words, sentences, paragraphs, speaking time,
share of words, and share of time, with inline bars drawn as styled divs.
Beneath it, a horizontal talk-flow strip showing the conversation’s speaker sequence at
a glance, which reads as a companion to the vertical rail.

Being a real table means it prints, it is screen-reader navigable, and it can be copied
into a spreadsheet.

### The concept map

Two views, both driven by the same data.

**Concept ribbon.** A swimlane chart: time on the horizontal axis, one row per concept,
bars where the concept is discussed.
This is the direct answer to seeing how concepts fit together on a timeline — sequence,
overlap, and clustering all read immediately.

**Concept graph.** A node-link diagram using a **time-layered layout** rather than a
force simulation: nodes are positioned along one axis by first-mention time and packed
along the other to avoid overlap, with relations drawn as curved edges.
Deterministic, no animation loop, no dependency, and considerably more readable than a
force blob, because the conversation’s own chronology supplies the layout’s primary
axis.

Selecting a concept in either view filters the rail to its spans and highlights its
mentions in the prose at runtime.
Highlighting is applied by the client and never written into the source HTML, so the
document and the PDF are unaffected.

A plain, always-present definition list of concepts and glosses sits beneath both views.
That list is what prints, and what a screen reader encounters.

### API changes

**`TranscribeOptions`** gains two fields:

```python
build_index: bool = False       # set with format=True; deterministic, no LLM cost
extract_concepts: bool = False  # opt-in; included in deep()
```

`formatted()` and `annotated()` set `build_index=True`. `deep()` additionally sets
`extract_concepts=True`.

**CLI** gains `--concepts` to request concept extraction on its own.
Concept background research reuses the existing `--web-search` flag rather than adding a
second search gate.

**New modules** in `src/deep_transcribe/`:

- `transcript_index.py` — index dataclasses, the pure builder, and the
  `attach_transcript_index` action.
- `concept_map.py` — the concept schema, prompt, and `extract_concepts` action.

## Implementation Plan

### Phase 1: Deterministic time-mapped view

Everything here is computable without an LLM and testable against the cached workspace,
so it can be built and reviewed at zero API cost.

- [ ] Add `transcript_index.py` with the index dataclasses and a pure
  `build_transcript_index(body, metadata, duration)` function.
- [ ] Resolve sentence-level timings by running the existing alignment at sentence
  granularity and keeping only the numbers.
- [ ] Read media duration and the speaker roster from workspace metadata; handle both
  being absent.
- [ ] Add the `attach_transcript_index` action and wire it into `_process_transcript` as
  the last stage.
- [ ] Add the guard test pinning that `minify_html` leaves the JSON island intact.
- [ ] Add `dt_core.js.jinja`: index parsing, DOM binding by citation key, time↔pixel
  math, the event contract, and the absent-index no-op path.
- [ ] Add `dt_viz.css.jinja` with the speaker palette, light and dark variants, and
  print rules that hide all interactive chrome.
- [ ] Add `dt_rail.js.jinja`: bucketed speaker band, section and frame ticks, viewport
  window, reading marker, hover tooltip, click-to-scroll, shift-click-to-seek, keyboard
  navigation, and popover coexistence.
- [ ] Add `dt_stats.js.jinja`: the speaker analytics table and talk-flow strip.
- [ ] Add `dt_frames.js.jinja`: gutter placement, the connector overlay, viewport-scoped
  drawing, and bidirectional hover.
- [ ] Extend `deep_transcribe_webpage.html.jinja` to include the new partials.
- [ ] Verify the printed PDF against `docs/examples/snl-hotel-check-in-transcript.pdf`.

### Phase 2: Concepts

- [ ] Add `concept_map.py` with the concept schema, the closed relation vocabulary, and
  the extraction prompt.
- [ ] Validate every mention timestamp against the index; drop and log unresolvable
  ones.
- [ ] Add the optional research pass behind `--web-search`, with sources and provenance
  preserved and search results barred from introducing concepts.
- [ ] Merge concepts into the index before serialization.
- [ ] Add `--concepts`; set `extract_concepts=True` in `deep()`.
- [ ] Add `dt_concepts.js.jinja`: concept ribbon, time-layered graph, selection
  filtering, runtime prose highlighting, and the printable definition list.
- [ ] Add the concept-span lane to the rail.

## Testing Strategy

**Python unit tests**, colocated in-module as this project does.
The index builder is a pure function over a body string plus metadata, so it tests
directly: paragraph and sentence timing, end-time derivation, the missing-duration
fallback, roster fallback when no roster is present, counts against known fixtures, and
unresolvable concept mentions being dropped.

**Golden tests.** A golden JSON index for the cached hotel-showcase document, and
updates to `tests/tryscript/cli.tryscript.md` for the new flag and help text.

**Structural HTML tests.** Render the cached document and assert on the output: the JSON
island survives minification and parses, every `key` in the index resolves to a
`data-timestamp` in the DOM, and every frame in the index matches an
`img.frame-capture`. This is where JavaScript correctness is pinned without adding a JS
test runner: the contract between index and DOM is the part that actually breaks, and it
is checkable in Python.

**Manual QA**, added to `tests/e2e-test.runbook.md`: rail tracking while scrolling,
hover tooltips, click-to-scroll and shift-click-to-seek, connector drawing at several
widths, the gutter breakpoint, light and dark themes, the rail yielding to an open
popover, keyboard navigation, and `prefers-reduced-motion`.

**Print regression.** Re-print the example and compare against the committed PDF. Any
visual difference in the printed output is a defect in this feature.

**Test beds.** `tmp/hotel-showcase/output/workspace` has every pipeline step cached, so
HTML can be re-rendered from `docs/watch_1_step12_insert_frame_captures_1.doc.md` in
seconds with no API keys and no network.
That is the inner loop.
The public SNL sketch (`kq9Q9-U0vrc`) is the outer loop and the showcase: five speakers
make the color palette, the speaker statistics, and the talk-flow strip meaningful in a
way a two-person conversation cannot.
A long-form podcast should be run once before merge purely to check rail bucketing and
connector performance at scale.

## Rollout Plan

Phase 1 ships as a default part of every formatted run.
It costs no API calls, adds no latency worth measuring, and degrades to today’s page
whenever the index is missing.

Phase 2 ships opt-in behind `--concepts` and inside `--deep`, so the flagship README
command keeps its current cost and runtime.

The README example is regenerated once Phase 1 lands, with a screenshot showing the rail
and connectors. The committed PDF is regenerated only if the print comparison shows it
should be, which by design it should not.

## Open Questions

- Should the index also be written as sidematter JSON next to the document, so external
  tools can consume it without parsing HTML? Cheap to add and plausibly useful, but it
  is scope beyond the view itself.
- How many concepts is right for a two-hour podcast?
  A four-minute sketch yields perhaps six.
  An hour-long interview could yield eighty, which no ribbon renders legibly.
  A cap with a two-level hierarchy — themes containing concepts — is the likely answer,
  but it should be decided against a real long transcript rather than in the abstract.
- Where exactly does the rail sit at intermediate widths, between the text column ending
  and the TOC breakpoint at 1200px? Needs to be settled by looking at it.
- Reader-authored annotations were explicitly deferred.
  Worth confirming that the event contract in `dt_core` is general enough that adding
  them later is additive rather than a redesign.

## References

- `docs/project/specs/active/plan-2026-08-26-snl-example-single-command-cli.md` — the
  CLI and SNL example this builds on
- `src/deep_transcribe/transcribe_commands.py` — pipeline stage ordering and HTML export
- `src/deep_transcribe/timestamp_citations.py` — citation markup this feature binds to
- `kash.kits.media.actions.transcribe.backfill_timestamps` — the alignment reused for
  sentence timings
- `kash.kits.media.actions.transcribe.insert_frame_captures` — frame markup and
  placement
- `kash.media_base.timestamp_citations` — the `data-timestamp` and `data-speaker-id`
  contract
- `kash/web_gen/templates/components/` — the component pattern the new modules follow

Related open work this feature must stay compatible with:

- `dt-g786` — remove load-time CDN dependencies from transcript HTML. The
  zero-dependency choice here is not just aesthetic; adding a CDN charting library would
  work directly against this.
- `dt-a5iy` — portable transcript HTML and ZIP bundle exports.
  Inlined modules and a self-contained JSON index bundle cleanly; anything fetched at
  load time would not.
- `dt-z68d` — automated portability checks for transcript exports.
  The new modules should pass those checks unchanged once they land.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
