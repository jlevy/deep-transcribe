---
type: is
id: is-01m1saq5qmcj906h8cg2yfs4m7
title: One unified concept graph with visible theme grouping
kind: feature
status: closed
priority: 2
version: 2
spec_path: docs/project/specs/active/plan-2026-09-04-agent-iteration-loop.md
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-05T17:44:03.059Z
updated_at: 2026-09-05T18:23:40.794Z
closed_at: 2026-09-05T18:23:40.793Z
close_reason: "one graph in labeled theme bands, edges across bands, chips flowing in clock order with 9rem labels in the graph only: 103 concepts, 11 bands, 37 rows, 1,573px, 0 overlaps; print same. Verified in the browser; 6b8df94."
resolution: null
duplicate_of: null
---
Owner: the per-theme graphs hidden under collapsed theme toggles make the concept graph invisible. Make it one graph that shows every node, grouped so the themes are still legible: e.g. one SVG with x = time (as today), nodes clustered by theme into labelled bands or hulls, edges drawn across themes, theme headers acting as filters/highlights rather than toggles that hide. Keep the per-theme definition lists collapsible if useful, but the graph itself always shows all nodes. Design first (a sketch of the layout at 100-300 nodes), then implement in dt_concepts.js.jinja; keep the resize behaviour from R10; verify on the Lex #501 export (103 concepts, 11 themes) in the browser and in print. This partly reverses 1e3b235 (per-theme graphs) and dt-4zij (clusters not bars) is related.
