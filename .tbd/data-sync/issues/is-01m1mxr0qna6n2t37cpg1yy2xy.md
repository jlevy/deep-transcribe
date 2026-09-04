---
type: is
id: is-01m1mxr0qna6n2t37cpg1yy2xy
title: One concept chip component for list and graph
kind: task
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-31-transcript-timeline-and-concept-map.md
labels: []
dependencies: []
created_at: 2026-09-04T00:40:21.492Z
updated_at: 2026-09-04T00:43:35.000Z
closed_at: 2026-09-04T00:43:35.000Z
close_reason: "Verified on the SNL test bed: graph chips and list chips render identically, ontology normalized in the live island (5 topic / 5 entity / 2 claim), transcript layout confirmed by capture"
resolution: null
duplicate_of: null
---
A single chip renders a concept everywhere: kind-colored outlined box containing the caps kind tag, a small dividing bar, and the medium-weight value. The definition list, Claims panel, and the concept graph all use the same component — the graph places the actual HTML chips over an SVG that draws only edges, so the two renderings are identical by construction.
