---
type: is
id: is-01m10wjnjn89mhyndnkk1d48an
title: Preserve cache lineage when paragraph breaking is a no-op
kind: bug
status: in_progress
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-26-snl-example-single-command-cli.md
labels: []
dependencies:
  - type: blocks
    target: is-01m10rzsv6hrkq26y5kf7r7a8q
parent_id: is-01m10ryb6ze39bmjjq0chrxpbx
created_at: 2026-08-27T05:55:09.011Z
updated_at: 2026-08-27T06:13:35.568Z
---
Kash’s per-item executor returns the original stored item when an action raises SkipItem, then records the skipped operation as that item’s source. This erases upstream lineage and forces downstream cache misses. Fix SkipItem handling in kash-shell so skipped items preserve their source and are not resaved, add an executor regression test, retain Kash Docs’ existing no-op action semantics, and verify Deep Transcribe can cache through paragraph and timestamp formatting.

## Notes

Pre-commit review moved the fix from a Kash Docs action workaround to the reusable Kash executor boundary. Local Kash changes pass Ruff and 10 focused tests.
