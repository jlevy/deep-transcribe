---
type: is
id: is-01m10wvqgjer8jbhx22ncvbc8r
title: Add an instruction-keyed overview cache boundary
kind: bug
status: closed
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-26-snl-example-single-command-cli.md
labels: []
dependencies:
  - type: blocks
    target: is-01m10rzsv6hrkq26y5kf7r7a8q
parent_id: is-01m10ryb6ze39bmjjq0chrxpbx
created_at: 2026-08-27T06:00:05.905Z
updated_at: 2026-08-27T06:59:05.779Z
closed_at: 2026-08-27T06:59:05.779Z
close_reason: Implemented in Deep Transcribe with focused regressions, full local gates, and a live instruction-only cache-reuse proof.
resolution: null
duplicate_of: null
---
Output-only instructions are correctly absent from raw and formatting inputs, but attaching them only in memory before add_transcript_outline means Kash hashes the stored instruction-free sectioned file and may reuse a stale overview. Add a deterministic derived boundary action keyed by the processing-instructions parameter, preserve the upstream cached item, add regression coverage, and prove changed instructions start at this boundary.

## Notes

Focused Deep Transcribe regression tests, Ruff, and BasedPyright pass. Live instruction-only rerun completed without another Deepgram call. Pre-commit review also fixed persistence of the restored source instructions.
