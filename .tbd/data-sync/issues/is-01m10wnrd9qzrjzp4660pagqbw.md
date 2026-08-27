---
type: is
id: is-01m10wnrd9qzrjzp4660pagqbw
title: Declare section-heading Markdown output contract
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
created_at: 2026-08-27T05:56:50.216Z
updated_at: 2026-08-27T06:13:36.229Z
---
Kash Docs insert_section_headings accepts Markdown-with-HTML but llm_transform_item emits a Markdown document. Declare output_type=doc and output_format=markdown with regression coverage so instruction-only refinements reuse section headings.

## Notes

Kash Docs section-heading output contract passes Ruff and its focused embedded test. Full native-repository CI will run on the upstream PR because the shared Deep Transcribe environment lacks Kash Docs’ repo-only document extras.
