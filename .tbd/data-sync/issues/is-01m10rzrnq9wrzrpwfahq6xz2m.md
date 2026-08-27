---
type: is
id: is-01m10rzrnq9wrzrpwfahq6xz2m
title: Implement the unified parser and --models flag
kind: feature
status: in_progress
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-08-26-snl-example-single-command-cli.md
labels: []
dependencies:
  - type: blocks
    target: is-01m10rzs362ec4pqvqffqw118r
  - type: blocks
    target: is-01m10rzsv6hrkq26y5kf7r7a8q
parent_id: is-01m10ryb6ze39bmjjq0chrxpbx
created_at: 2026-08-27T04:52:23.862Z
updated_at: 2026-08-27T04:59:08.522Z
---
Remove subparsers, command routing, and the direct-parser fork. Build one parser and dispatch path; implement --models with active workspace reporting, persistent selection, and optional continuation into transcription.

## Notes

Implementation started after the CLI contract tests failed against the current subparser and direct-parser fork.
