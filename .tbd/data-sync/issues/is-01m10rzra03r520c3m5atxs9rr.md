---
type: is
id: is-01m10rzra03r520c3m5atxs9rr
title: Define the single-command CLI contract with failing tests
kind: task
status: closed
priority: 1
version: 6
spec_path: docs/project/specs/active/plan-2026-08-26-snl-example-single-command-cli.md
labels: []
dependencies:
  - type: blocks
    target: is-01m10rzrnq9wrzrpwfahq6xz2m
  - type: blocks
    target: is-01m10rzsfvq0ramn2v7xez900n
  - type: blocks
    target: is-01m10s3fq85s3f5hrb4ea83n1p
parent_id: is-01m10ryb6ze39bmjjq0chrxpbx
created_at: 2026-08-27T04:52:23.486Z
updated_at: 2026-08-27T05:03:55.547Z
closed_at: 2026-08-27T05:03:55.547Z
close_reason: Implemented and committed in c3f9217. The CLI now has one direct-source parser and help surface; --models lists, persists, reports, and can continue into transcription. Lint/type checks, 65 tests, and builds pass.
resolution: null
duplicate_of: null
---
Specify the direct-source parser, one-page help groups, optional target validation, and optional-value --models list/set/continue semantics as focused parser and subprocess tests before implementation.

## Notes

TDD red established in tests/test_cli.py for the direct-source parser, one-page help, optional --models action, and no-source validation.
