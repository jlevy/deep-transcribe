---
type: is
id: is-01m10s3fq85s3f5hrb4ea83n1p
title: Infer speaker rosters from ordinary-prose context
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
created_at: 2026-08-27T04:54:25.764Z
updated_at: 2026-08-27T05:24:02.017Z
closed_at: 2026-08-27T05:24:02.017Z
close_reason: Implemented bounded delimiter-safe source evidence, prose-to-roster inference with explicit override precedence, and a deterministic Tryscript golden for the unified CLI; full lint, type, Python, and golden tests pass.
resolution: null
duplicate_of: null
---
When reviewed prose explicitly names a complete set of speaking roles, use a structured LLM step to derive the internal speaker roster and label policy. Exact speaker-role and speaker-ID inputs remain authoritative overrides; ambiguous prose must fail closed instead of inventing participants.
