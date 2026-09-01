---
type: is
id: is-01m1dbnh792dzcbyjhy5a9rqda
title: Build the deterministic transcript index
kind: feature
status: open
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-08-31-transcript-timeline-and-concept-map.md
labels: []
dependencies:
  - type: blocks
    target: is-01m1dbnhjqwmq7h2wj4fb3ztcb
  - type: blocks
    target: is-01m1dbp059hmx278czczgmhjtm
parent_id: is-01m1dbmypatm5c5e8sbhzqmphd
created_at: 2026-09-01T02:09:44.679Z
updated_at: 2026-09-01T02:10:31.210Z
---
Add src/deep_transcribe/transcript_index.py: index dataclasses plus a pure build_transcript_index() over the document body, workspace metadata, and media duration. Resolve sentence-level timings by running the existing backfill_timestamps alignment at sentence granularity and keeping only the numbers. Derive unit end times from the next unit's start, with a documented fallback when duration is unavailable. Count words/sentences/paragraphs with flexdoc so the numbers match the rest of the pipeline. Add the attach_transcript_index action, wire it in as the last stage of _process_transcript, and emit the index as a hidden application/json island keyed by citation timestamp. Include the guard test pinning that minify_html leaves the island intact.
