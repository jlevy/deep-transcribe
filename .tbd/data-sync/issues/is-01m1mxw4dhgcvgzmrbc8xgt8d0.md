---
type: is
id: is-01m1mxw4dhgcvgzmrbc8xgt8d0
title: Fix the concept ontology to topic, entity, claim
kind: task
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-31-transcript-timeline-and-concept-map.md
labels: []
dependencies: []
created_at: 2026-09-04T00:42:36.335Z
updated_at: 2026-09-04T00:43:35.009Z
closed_at: 2026-09-04T00:43:35.009Z
close_reason: "Verified on the SNL test bed: graph chips and list chips render identically, ontology normalized in the live island (5 topic / 5 entity / 2 claim), transcript layout confirmed by capture"
resolution: null
duplicate_of: null
---
The kind vocabulary is now exactly topic, entity, and claim. decision folds into claim and term into topic, both at parse time and when resolving stored concepts, so older extractions normalize cleanly. Prompt, Claims panel filter, kind colors, and tests updated.
