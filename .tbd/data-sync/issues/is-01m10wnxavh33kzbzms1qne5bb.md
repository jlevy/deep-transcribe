---
type: is
id: is-01m10wnxavh33kzbzms1qne5bb
title: Declare Deep Transcribe outline Markdown-HTML output contract
kind: bug
status: closed
priority: 1
version: 6
spec_path: docs/project/specs/active/plan-2026-08-26-snl-example-single-command-cli.md
labels: []
dependencies:
  - type: blocks
    target: is-01m10rzsv6hrkq26y5kf7r7a8q
parent_id: is-01m10ryb6ze39bmjjq0chrxpbx
created_at: 2026-08-27T05:56:55.258Z
updated_at: 2026-08-27T06:59:05.771Z
closed_at: 2026-08-27T06:59:05.771Z
close_reason: Implemented in Deep Transcribe with focused regressions, full local gates, and a live instruction-only cache-reuse proof.
resolution: null
duplicate_of: null
---
add_transcript_outline wraps a Markdown sectioned transcript in Markdown-with-HTML but its action preassembly inherits Markdown. Declare the output contract and test it so identical overview requests can reuse the saved outline.

## Notes

Focused Deep Transcribe regression tests, Ruff, and BasedPyright pass. Live instruction-only rerun completed without another Deepgram call.
