---
type: is
id: is-01m1mjf4w3ytt4zk6ps0eks43z
title: Raise hovered gutter frames with a delayed restore
kind: task
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-31-transcript-timeline-and-concept-map.md
labels: []
dependencies: []
parent_id: is-01m1mjdr6qh7awq6dxje4kgzne
created_at: 2026-09-03T21:23:16.481Z
updated_at: 2026-09-03T21:31:34.528Z
closed_at: 2026-09-03T21:31:34.528Z
close_reason: Implemented and verified on the SNL test bed (light/dark, headless captures + in-browser selection checks)
resolution: null
duplicate_of: null
---
Hovering a frame capture in the gutter lifts it above any overlapping neighbors with a smooth transition; after the pointer leaves it stays on top briefly (tooltip-style delay) before settling back into its usual stacking.
