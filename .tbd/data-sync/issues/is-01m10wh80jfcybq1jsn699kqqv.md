---
type: is
id: is-01m10wh80jfcybq1jsn699kqqv
title: Declare Kash strip_html Markdown output for cache preassembly
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
created_at: 2026-08-27T05:54:22.353Z
updated_at: 2026-08-27T06:59:04.850Z
closed_at: 2026-08-27T06:59:04.850Z
close_reason: Implemented upstream in kash-shell 0.4.9; PR, CI, release, and installed smoke all passed.
resolution: null
duplicate_of: null
---
After raw and speaker stages began hitting cache, the live trace showed Kash strip_html still reruns because preassembly inherits the HTML input format while the action emits Markdown. Declare output_format=markdown, add a focused output-contract test, and verify the Deep Transcribe refinement trace continues through the formatting chain.

## Notes

Local Kash source changes have focused regression coverage and pass Ruff plus 10 focused tests. Full native-repository CI will run on the upstream PR because Deep Transcribe’s shared environment has incompatible optional MCP test dependencies.
