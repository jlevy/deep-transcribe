---
type: is
id: is-01m1q210z9ratqj6skv0bzwv1m
title: "PR #19 review R7: suggested hint spans are rounded off the paragraphs they describe"
kind: bug
status: in_progress
priority: 1
version: 2
labels: []
dependencies: []
parent_id: is-01m1q1zs4f81krjzenfbtmp35t
created_at: 2026-09-04T20:33:39.816Z
updated_at: 2026-09-04T20:46:50.085Z
---
segment_hints / detect_segments writes spans rounded to whole seconds (or coarser), so the emitted span can start after the paragraph it means to cover, and a rerun with the suggested file excludes the wrong units. Write the exact unit boundaries.
