---
type: is
id: is-01m10wnk8b69y5h4vpvydj5mrc
title: Declare timestamp backfill Markdown-HTML output contract
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
created_at: 2026-08-27T05:56:44.937Z
updated_at: 2026-08-27T06:13:36.006Z
---
Kash Media backfill_timestamps converts Markdown to Markdown-with-HTML citations but does not declare output_type=doc and output_format=md_html. Add the declarations and regression coverage so cache preassembly can find saved timestamped transcripts.

## Notes

Kash Media output contracts pass Ruff and four focused embedded tests against local first-party source checkouts; the earlier full package suite passed 14 tests.
