---
type: is
id: is-01m1nax6vqj3dqbc25qp7hk7nf
title: Extract concepts per chunk and merge
kind: feature
status: open
priority: 0
version: 1
spec_path: docs/project/specs/active/plan-2026-09-04-chunked-extraction.md
labels: []
dependencies: []
parent_id: is-01m1nax66j442h166dee52zt3r
created_at: 2026-09-04T04:30:23.093Z
updated_at: 2026-09-04T04:30:23.093Z
---
Make MAX_CONCEPTS per-chunk (8-12) instead of per-recording, so a 5h episode yields ~50-70 concepts and 12h ~120-170 while a short talk is unchanged. Merge by normalized id then label: union mentions and speakers, span from earliest to latest, first non-empty gloss. Resolve relations ONCE over the merged set so a relation naming a concept from another chunk survives.
