---
type: is
id: is-01m10v3kvfn09bvkxf65kzmzj8
title: Keep synopsis and outline instructions stage-specific
kind: bug
status: in_progress
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-08-26-snl-example-single-command-cli.md
labels: []
dependencies:
  - type: blocks
    target: is-01m10rzsv6hrkq26y5kf7r7a8q
parent_id: is-01m10ryb6ze39bmjjq0chrxpbx
created_at: 2026-08-27T05:29:27.150Z
updated_at: 2026-08-27T06:13:34.448Z
---
The live SNL annotated run reached add_transcript_outline, but shared processing instructions mentioned both synopsis and outline. The outline model followed the synopsis sentence and returned two paragraphs, which the strict outline validator correctly rejected. Scope each overview prompt to its own output form, add focused regression coverage, and prove the cached rerun completes without another Deepgram call.

## Notes

Focused Deep Transcribe regression tests, Ruff, and BasedPyright pass. Live instruction-only rerun completed without another Deepgram call.
