---
type: is
id: is-01m1n3w3s56t6zzyf0e8zbzcaq
title: Apply exclusions with boundary snapping
kind: feature
status: open
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-09-04-transcript-segments.md
labels: []
dependencies: []
parent_id: is-01m1n3q978x6fyhsyfm175ngy6
created_at: 2026-09-04T02:27:27.139Z
updated_at: 2026-09-04T04:09:12.531Z
---
--exclusions FILE truncates content inside the given ranges. The unit of exclusion is the paragraph: for each proposed boundary the resolver seeks BOTH directions from that time and takes the nearest candidate by strength — paragraph break, else sentence break, else citation timestamp — with a paragraph break within tolerance beating a nearer sentence break. Ties of equal strength go to the option that excludes less (later start, earlier end) so a snap never eats surviving speech; ranges that would invert or empty are dropped with a warning. Reuses the same bidirectional token seeking backfill_timestamps already uses. Transcription is untouched, so the second run reuses the raw cache and starts at the formatting boundary.
