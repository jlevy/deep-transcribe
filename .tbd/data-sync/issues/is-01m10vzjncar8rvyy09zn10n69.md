---
type: is
id: is-01m10vzjncar8rvyy09zn10n69
title: Declare Kash Media transcription output type for cache preassembly
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
created_at: 2026-08-27T05:44:43.435Z
updated_at: 2026-08-27T06:13:35.789Z
---
Kash preassembles kash-media transcribe outputs as URL resources because the action does not declare its output type and format, while the saved result is an HTML document. ItemId includes type, so cache lookup cannot match. Declare the output contract upstream, add a focused cache/preassembly regression test, test Deep Transcribe against the local checkout, and coordinate the patch release before Deep Transcribe.

## Notes

Kash Media output contracts pass Ruff and four focused embedded tests against local first-party source checkouts; the earlier full package suite passed 14 tests.
