---
type: is
id: is-01m1nax75yngmqmeeempej0hke
title: Chunk the outline and reduce the synopsis
kind: feature
status: open
priority: 0
version: 5
spec_path: docs/project/specs/active/plan-2026-09-04-chunked-extraction.md
labels: []
dependencies:
  - type: blocks
    target: is-01m1ng5b07vkx3hx5ghky3sxf5
parent_id: is-01m1nax66j442h166dee52zt3r
created_at: 2026-09-04T04:30:23.422Z
updated_at: 2026-09-04T07:32:02.996Z
---
Outline is already sectional, so per-chunk outlines concatenate in timeline order. Synopsis becomes map-reduce: per-chunk summaries, then a final pass over those summaries.

The reduce pass reads STRUCTURE, not text: a 5-hour transcript is 55k words but its outline is ~2k and 50-70 concepts with glosses about the same, so the reduce input is article-sized at any recording length. That headroom lets it genuinely organize rather than just concatenate — collapse near-duplicates that identity matching misses ('AI coding agents' vs 'agentic coding'), group concepts into themes once a flat list stops being a map, order the outline as a progression, and prune concepts that prove minor once the whole conversation is in view.

## Notes

CONCEPTS HALF DONE in c649c5e. The reduce pass now runs over the merged map and groups
it into themes; the outline and synopsis halves of this bead are still open.

MEASURED on the 5.3-hour run:
  concepts             119 -> 115 (4 merged or dropped)
  themes               12, every concept placed
  definition list      18,399 px -> 729 px
  reduce call          one, on top of the 10 extraction calls; 780 s total

The themes are good and read as real strands of the conversation:
  AI progress and the agentic turn / Linux's agentic moment / Vibe coding, language and
  AI creativity / Open source and agentic contribution / Coping with AI disruption /
  Multi-agent workflow and infrastructure / Building Omarchy / Autonomous agents and AGI
  glimmers / Meaning, mortality and the long view / Politics, media and discourse / AI
  security, safety and censorship / AI agents in daily life and the web

DEDUPLICATION UNDERPERFORMED — worth another look, though it is the smaller half of the
win. Only 4 of 119 were merged or dropped. Survivors:
  "Glimmers of AI consciousness" (4:07) vs "Glimmers of AGI in coding agents" (2:57),
    and they landed in different themes, which is worse than leaving them adjacent.
  "'AI psychosis' / delirium debate" vs "AI psychosis from predicting the future" —
    arguably two distinct claims, so this one may be correct.
The prompt tells the model to be conservative about DROPPING; it looks like that caution
generalized to merging. Splitting the two instructions, or asking for merges in a
separate pass from the pruning, is the obvious thing to try.

Note the Omarchy/Omakub/Omarchi/Omachi spread is partly a transcription artifact of a
hard proper noun and partly real — Omakub and Omarchy are different projects — so it is
not a fair test of the merge.

Still open on this bead: chunk the outline, reduce the synopsis, and order the outline
as a progression. Those still send the whole document (dt-2sam).
