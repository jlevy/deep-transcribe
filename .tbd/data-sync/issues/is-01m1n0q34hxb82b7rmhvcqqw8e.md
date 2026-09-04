---
type: is
id: is-01m1n0q34hxb82b7rmhvcqqw8e
title: Wrap timeline section labels onto two lines
kind: task
status: closed
priority: 2
version: 3
spec_path: docs/project/specs/active/plan-2026-09-03-dt-design-system-refactor.md
labels: []
dependencies: []
created_at: 2026-09-04T01:32:16.912Z
updated_at: 2026-09-04T01:34:15.717Z
closed_at: 2026-09-04T01:34:15.717Z
close_reason: Implemented and verified on the SNL test bed by capture and headless DOM checks; 100 tests and goldens green
resolution: null
duplicate_of: null
---
Section names in Timeline blocks wrap to two balanced lines via tspans instead of truncating early with an ellipsis; one line stays vertically centered, two lines split at the best word boundary, and an ellipsis appears only when even two lines cannot hold the name.
