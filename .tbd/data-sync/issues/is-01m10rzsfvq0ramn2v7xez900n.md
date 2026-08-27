---
type: is
id: is-01m10rzsfvq0ramn2v7xez900n
title: Audit and complete YouTube source-context propagation
kind: feature
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-26-snl-example-single-command-cli.md
labels: []
dependencies:
  - type: blocks
    target: is-01m10rzsv6hrkq26y5kf7r7a8q
parent_id: is-01m10ryb6ze39bmjjq0chrxpbx
created_at: 2026-08-27T04:52:24.698Z
updated_at: 2026-08-27T05:24:02.008Z
closed_at: 2026-08-27T05:24:02.007Z
close_reason: Implemented bounded delimiter-safe source evidence, prose-to-roster inference with explicit override precedence, and a deterministic Tryscript golden for the unified CLI; full lint, type, Python, and golden tests pass.
resolution: null
duplicate_of: null
---
Trace extractor metadata through source and cached transcript items into semantic prompts. Preserve bounded title, channel, date, description, and URL as delimited untrusted evidence; add only missing local behavior with synthetic propagation and prompt-safety tests.
