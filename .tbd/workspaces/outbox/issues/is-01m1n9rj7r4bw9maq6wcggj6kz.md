---
type: is
id: is-01m1n9rj7r4bw9maq6wcggj6kz
title: Detect preview clips by near-duplicate matching
kind: feature
status: closed
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-09-04-transcript-segments.md
labels: []
dependencies: []
parent_id: is-01m1n3q978x6fyhsyfm175ngy6
created_at: 2026-09-04T04:10:22.326Z
updated_at: 2026-09-04T09:20:55.245Z
closed_at: 2026-09-04T09:20:55.243Z
close_reason: Implemented in 40b6ab1. Five-word shingle matching against the rest of the recording, tolerating one spliced-in narration paragraph. On the real transcript it finds 0:00:04-0:01:48 at 100% echoed, stopping correctly before the host's introduction — more precise than the section boundaries suggested. Writes segments.suggested.yml and never overwrites existing hints.
resolution: null
duplicate_of: null
---
MEASURED on Lex #501: 14 of 15 substantive sentences in the 'Episode highlight' chapter are near-verbatim repeats of later material (similarity 0.97-1.00) drawn from seven separate points across five hours. A teaser is assembled from later audio, so near-duplicate matching detects it mechanically and near-certainly — no model call, and immune to the failure mode of mistaking genuine restatement for a teaser, since real restatement is paraphrase rather than fourteen verbatim sentences from seven places.
