---
type: is
id: is-01m1mwfc1c80wnc3zt13mrf31v
title: Render the Timeline at 1:1 pixels with design-system type
kind: task
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-31-transcript-timeline-and-concept-map.md
labels: []
dependencies: []
created_at: 2026-09-04T00:18:09.578Z
updated_at: 2026-09-04T00:20:04.827Z
closed_at: 2026-09-04T00:20:04.827Z
close_reason: Implemented and verified on the SNL test bed; timeline type at design-system sizes confirmed by capture
resolution: null
duplicate_of: null
---
The overview SVG scaled its 720-unit viewBox down, shrinking 9px labels to ~7.5px. Render at the panel's real pixel width via ResizeObserver so axis and section labels use the design-system sizes exactly (font-size-tiny). Axis times lose their brackets: on a timeline the position says it is a time; brackets remain for timestamps inline with text. Concept ribbon and graph label sizes bumped to match visually.
