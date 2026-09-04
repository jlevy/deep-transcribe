---
type: is
id: is-01m1my0wkd2g6m2b1y7g4byd6q
title: Per-concept timeline bars above each list entry
kind: task
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-31-transcript-timeline-and-concept-map.md
labels: []
dependencies: []
created_at: 2026-09-04T00:45:12.169Z
updated_at: 2026-09-04T00:49:55.215Z
closed_at: 2026-09-04T00:49:55.214Z
close_reason: "Verified on the SNL test bed: tracks aligned with the Timeline scale, mention tooltips show transcript excerpts, headings uniformly black, single chip rendering"
resolution: null
duplicate_of: null
---
The standalone concept ribbon goes away. The Concepts panel is now graph on top, then the list, where every entry stacks: a full-width mini timeline (track, kind-colored span, clickable mention dots scaled to the media duration), then the concept chip with its time, then the gloss. Entries become divs (a dl cannot hold the track rows); selection still dims and highlights entries.
