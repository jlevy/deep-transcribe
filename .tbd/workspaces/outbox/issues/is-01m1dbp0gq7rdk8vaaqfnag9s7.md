---
type: is
id: is-01m1dbp0gq7rdk8vaaqfnag9s7
title: Render the concept ribbon and time-layered concept graph
kind: feature
status: open
priority: 2
version: 2
spec_path: docs/project/specs/active/plan-2026-08-31-transcript-timeline-and-concept-map.md
labels: []
dependencies: []
parent_id: is-01m1dbmypatm5c5e8sbhzqmphd
created_at: 2026-09-01T02:10:00.342Z
updated_at: 2026-09-01T02:10:33.500Z
---
Add dt_concepts.js.jinja: a swimlane ribbon (time on x, one row per concept, bars where discussed) and a node-link graph using a deterministic time-layered layout, positioning nodes by first-mention time and packing to avoid overlap, with no force simulation and no dependency. Selecting a concept filters the rail and highlights its mentions in the prose at runtime only, never in the source HTML. Include an always-present definition list of concepts and glosses as the printable and screen-reader fallback. Add the concept-span lane to the rail.
