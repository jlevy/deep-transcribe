---
type: is
id: is-01m1mx2ekn667ebg8wmz3fe74r
title: Color the kind chips by type with visible borders
kind: task
status: closed
priority: 2
version: 4
spec_path: docs/project/specs/active/plan-2026-08-31-transcript-timeline-and-concept-map.md
labels: []
dependencies: []
created_at: 2026-09-04T00:28:34.801Z
updated_at: 2026-09-04T00:32:14.563Z
closed_at: 2026-09-04T00:32:14.562Z
close_reason: "Verified on the SNL test bed: kind colors on chips and graph tags confirmed by capture, band tooltip text and sans labels confirmed in rendered DOM"
resolution: null
duplicate_of: null
---
The TOPIC/ENTITY/CLAIM/DECISION/TERM chips get their kind's color on text and border (replacing faint border-hint gray) via a shared --dt-kind-c variable; the same caps kind tag now appears inside each concept-graph node; and the stylesheet collapses to two radius tokens (--dt-radius 0.25rem for small controls, --dt-radius-lg 0.4rem for surfaces), with graph nodes, section blocks, and ribbon spans all on the small radius like the chips.
