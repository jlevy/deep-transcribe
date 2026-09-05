---
title: Theme Grouping Across the Page
description: One rule for when a long recording's outline, concepts, claims, and graph group by theme; one graph of every concept with the themes visible as bands; and an export-time control so the rule can be tuned after seeing the page, without recomputing anything.
author: Joshua Levy with Claude assistance
---
# Feature: Theme Grouping Across the Page

**Date:** 2026-09-05

**Author:** Joshua Levy with Claude assistance

**Status:** Implemented on the branch; verified on Lex #501 and the SNL example

## Overview

A five-hour recording produces about 200 outline entries, 125 concepts, and 40 claims.
The long-form work grouped the first two by the themes the reduce pass finds, and it
decided *whether* to group three different ways: the outline groups when it has more
than 30 entries, the concept list collapses when it has more than 24 concepts, and the
claims list never groups. The concept graph, when the list is grouped, is cut into one
small graph per theme and hidden inside that theme's toggle.

The owner's review of the Lex #501 page found the shape wrong in three ways, and this
spec is the plan for the fix:

1. Hiding the graphs under toggles makes the graph invisible. There should be one graph
   of every concept, with the themes shown as grouping, not as separate charts.
2. The claims list is a wall; it should be grouped like the outline and the concepts.
3. Grouping is right for a recording of this length and wrong for a short one. The
   cutoff is somewhere between thirty minutes and an hour, it should be one heuristic
   rather than three counts, and it must be settable after seeing the page, with a
   rerun that costs seconds.

## Goals

- One rule, decided in one place, read by every view: group when the recording is at
  least the cutoff long and the reduce pass found at least two themes.
- One control, `--grouping`, that forces it on or off or sets the cutoff, and that
  travels in the page so `--export-only` re-applies it without an API call.
- One graph of every concept, always visible, with a labeled band per theme.
- The claims list grouped under the same theme heads as the outline and the concepts.
- A short recording renders exactly as it does today: flat lists, one flat graph.

## Non-Goals

- How themes are found. The reduce pass and its small-theme problem (dt-6615) are
  separate.
- Clustered concept tracks (dt-4zij).
- Any change to what is stored in the workspace. Grouping is a view decision.

## Background

### What exists

Themes come from the reduce pass in `concept_map.py`, which runs when concept extraction
used more than `REDUCE_THRESHOLD` chunks. Each kept concept carries a `theme`, and
concepts are ordered by theme and then by the clock. Short media that fits in one or two
chunks has no themes at all.

On the page, `dt_concepts.js.jinja` does the grouping. `buildThemeGroup` makes the head
(name, count, first-visit time, collapse toggle). The outline is regrouped by proximity
to the nearest concept's theme (`groupOutlineByTheme`, when the outline has more than
`OUTLINE_FLAT_LIMIT` entries). The definition list is grouped by the concepts' own
themes and collapsed when there are more than `FLAT_LIST_LIMIT`. With more than one
group, `layoutThemeGraphs` builds a graph per theme inside its group body, laid out on
the theme's own time span because a thirty-minute theme on a five-hour axis crowds into
the left tenth of the width. A single flat graph of everything is still built for print.

### What the review found

On the Lex #501 page (5 h 15 m, 13 themes, 124 concepts): the Concepts panel shows
thirteen collapsed heads and no graph until each is opened; the Claims panel is one
list of forty entries; the outline is grouped and reads well. The owner's direction is
quoted in the beads: dt-td4s (graph), dt-r25q (claims), dt-oa7n (the rule and its
control, "iteratively settable if something doesn't look right, then possible to rerun").

## Design

### The rule

```
grouped = mode == "on"
       or (mode != "off" and duration_seconds >= cutoff_minutes * 60)
```

and, whatever the mode, only when the index holds at least two themes, because there is
nothing to group by otherwise. `mode` is `on`, `off`, or `auto`; `cutoff_minutes`
defaults to 45, the middle of the range the owner named.

`dt_core.js.jinja` decides it once at load, reading `window.DT_GROUPING` and
`model.duration`, and exposes `model.grouped`. Every module reads that boolean. The three
count thresholds go: a recording past the cutoff has enough of everything, and one below
it is short enough to read flat.

### The control

`--grouping VALUE`, where `VALUE` is `on`, `off`, or a number of minutes (the cutoff).
Default `45`. It is an export setting: `inject_page_config` writes
`window.DT_GROUPING = {"mode": ..., "cutoff_minutes": ...}` next to `DT_ELEMENTS`, and
nothing in the workspace changes. The rerun table gains a row: change `--grouping`,
rerun with `--export-only`, seconds, no API calls. This is the "settable, then rerun"
shape the owner asked for, and it is the shape every future view setting should take.

`--grouping on` on a recording with no themes stays flat, and the report says so
(theme count 0), because forcing a view cannot invent the data it needs.

### The graph

One graph of every concept, in bands. Each theme is a band: a label line (theme name,
then the theme's time range in the timestamp style), then its chips in clock order,
flowing left to right and wrapping. Bands stack in the order the conversation reaches
the themes, separated by space and a faint ground, never a rule. Relation edges are
drawn in the one SVG, so an edge between themes crosses bands and is visible for the
first time. Selecting a chip dims the rest as before.

Inside a band the axis is ordinal, not time. The first build kept the per-theme time
axis and measured 3,512 px: a theme's concepts are introduced in one cluster of minutes
while the theme spans hours, so on a time axis they stack into a column (one theme took
23 rows for 24 chips). The second build flowed the chips and measured 3,083 px, because
the chips themselves are 245 to 390 px wide and the column is 606: one or two to a row.
So in the graph, and only there, a chip takes the tiny size and its label is clipped to
9rem with an ellipsis; the tooltip and the list carry the full label. Three chips to a
row, 37 rows, about 1,600 px for 103 concepts in 11 bands, with no overlap.

The band layout replaces both the per-theme graphs and their open-on-toggle re-layout.
The print graph is the same builder at `--dt-print-width`. A recording that is not
grouped gets one band with no label on the recording's time axis, which is exactly
today's flat graph.

### The lists

Outline and Concepts keep `buildThemeGroup`, now gated by `model.grouped` alone. Claims
gains the same: claims are already in theme order because the concept list is, so the
claims panel walks them with the same "open a group when the theme changes" loop the
definition list uses, collapsed by default, with "(N items)" on every head.

### Short recordings

Below the cutoff, or with `--grouping off`: flat outline, flat definition list, flat
claims, one flat graph. No code path is new; the gate is.

## Implementation Plan

### Phase 1: The rule and the control

- [x] `--grouping on|off|MINUTES`, validated in `cli_main.py`; `inject_page_config`
  writes `window.DT_GROUPING`; `model.grouped` decided in `dt_core.js.jinja`; the three
  count thresholds removed. Tests for the parser and the injection. (dt-oa7n)
- [x] `docs.md` rerun-table row and the flag in the skill's iteration section.

### Phase 2: The views

- [x] The banded graph, screen and print; per-theme graphs and their toggle-time layout
  removed. (dt-td4s)
- [x] Claims grouped under theme heads. (dt-r25q)
- [x] Verified in a browser. Lex #501: grouped, 103 chips in 11 labeled bands, 89 edges,
  0 overlaps, 77 claims in 9 groups with counts, outline in 9 groups; `--grouping off`
  on the same export: flat, no heads, one band. SNL (4 min, no themes): flat by default
  and flat with `--grouping on`, no error.

## Testing Strategy

The injection has a CLI-path test like the one for `--elements`. The view logic is
verified in a browser on the two reference recordings, one on each side of the cutoff,
and with `--grouping off` on the long one and `--grouping on` on the short one (which
must stay flat, with no error). Both are re-exports, so the whole check costs under a
minute.

## Open Questions

- The default cutoff. Forty-five minutes is the middle of the owner's range; a
  forty-minute recording with a dozen themes might argue for thirty. Decide after seeing
  one.
- Whether `--grouping on` should also make the reduce pass run on a short recording so
  that themes exist to group by. Today the reduce pass is gated on chunk count, not on
  this flag, and the flag is an export setting by design.

## References

- `plan-2026-09-04-long-form-stabilization.md`, Phase 4: the review round this came
  from.
- `plan-2026-08-31-transcript-timeline-and-concept-map.md`: the original graph design.
- `plan-2026-09-04-agent-iteration-loop.md`: `--export-only` and the recipe loop this
  control joins.
- Beads: dt-oa7n, dt-td4s, dt-r25q.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
