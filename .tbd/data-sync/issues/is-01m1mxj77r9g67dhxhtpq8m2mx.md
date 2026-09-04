---
type: is
id: is-01m1mxj77r9g67dhxhtpq8m2mx
title: Match kind-tag type between graph nodes and chips
kind: task
status: closed
priority: 2
version: 3
spec_path: docs/project/specs/active/plan-2026-08-31-transcript-timeline-and-concept-map.md
labels: []
dependencies: []
created_at: 2026-09-04T00:37:11.530Z
updated_at: 2026-09-04T00:43:34.984Z
closed_at: 2026-09-04T00:43:34.983Z
close_reason: "Verified on the SNL test bed: graph chips and list chips render identically, ontology normalized in the live island (5 topic / 5 entity / 2 claim), transcript layout confirmed by capture"
resolution: null
duplicate_of: null
---
The concept ribbon and graph now render at the panel's real pixel width (like the Timeline) instead of scaling a 720-unit viewBox, so the kind tag inside graph nodes uses exactly the standalone chips' size, weight, and caps treatment. Selection state survives re-renders.
