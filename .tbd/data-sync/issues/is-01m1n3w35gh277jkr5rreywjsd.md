---
type: is
id: is-01m1n3w35gh277jkr5rreywjsd
title: Add the detect_segments pass
kind: feature
status: open
priority: 2
version: 3
spec_path: docs/project/specs/active/plan-2026-09-04-transcript-segments.md
labels: []
dependencies: []
parent_id: is-01m1n3q978x6fyhsyfm175ngy6
created_at: 2026-09-04T02:27:26.511Z
updated_at: 2026-09-04T08:07:02.367Z
---
An LLM stage over the full transcript that proposes non-conversation spans, citing citation keys the way concept mentions do so every proposal traces to real timestamps; unresolvable proposals are dropped. Writes the exclusion file and changes nothing else. Exposed as --detect-segments, reporting what it found and the total time proposed.
