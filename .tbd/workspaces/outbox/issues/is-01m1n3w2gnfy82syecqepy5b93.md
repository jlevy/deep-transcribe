---
type: is
id: is-01m1n3w2gnfy82syecqepy5b93
title: Add the exclusion file format and IO
kind: feature
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-09-04-transcript-segments.md
labels: []
dependencies: []
parent_id: is-01m1n3q978x6fyhsyfm175ngy6
created_at: 2026-09-04T02:27:25.843Z
updated_at: 2026-09-04T09:07:59.356Z
closed_at: 2026-09-04T09:07:59.355Z
close_reason: Format, parser, writer and validation in 1c1f02f; CLI --segments in 1f56b83. Times read as H:MM:SS or seconds, spans as 'at' or start/end, purpose from a fixed vocabulary with suppression defaulting by purpose, malformed entries dropped with a warning rather than failing the run.
resolution: null
duplicate_of: null
---
A reviewable file listing timestamp ranges in kash's Slice vocabulary with kind (intro/sponsor/outro/duplicate), confidence, note, and an opening quote for orientation. Reader, writer, and validation.
