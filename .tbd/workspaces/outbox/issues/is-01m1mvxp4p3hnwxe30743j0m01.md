---
type: is
id: is-01m1mvxp4p3hnwxe30743j0m01
title: Replace native tooltips with one clean tooltip component
kind: task
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-31-transcript-timeline-and-concept-map.md
labels: []
dependencies: []
created_at: 2026-09-04T00:08:30.101Z
updated_at: 2026-09-04T00:13:58.282Z
closed_at: 2026-09-04T00:13:58.282Z
close_reason: "Implemented and verified on the SNL test bed: tooltip contract tested in-browser, file:// fallback verified headless with file access, palette AA-checked, print gate still green"
resolution: null
duplicate_of: null
---
A single reusable plain-JS tooltip: ~250ms show delay, fade in/out animation, viewport-clamped positioning, reduced-motion aware. All dt components use it (timeline sections, band segments, frame markers, concept graph nodes and edges) instead of native title/svg-title tooltips, which are removed; the rail's live-tracking tip drives the same component through its point API.
