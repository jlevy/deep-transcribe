---
type: is
id: is-01m0yf4tkmrvhwgn4q2ykkv0sr
title: Define built-in docs and skill contract with tests
kind: task
status: closed
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-26-self-documenting-skill.md
delegate: codex@spud10.local
labels:
  - testing
dependencies:
  - type: blocks
    target: is-01m0yf4vcv5n2nhq8bs703cq38
  - type: blocks
    target: is-01m0yf4vy1d0bt0e8zpz8yjh33
parent_id: is-01m0yf48parshvzra5k25xv9wr
hold: null
hold_until: null
created_at: 2026-08-26T07:21:55.017Z
updated_at: 2026-08-26T07:53:06.672Z
started_at: 2026-08-26T07:22:07.862Z
closed_at: 2026-08-26T07:33:35.383Z
close_reason: Implemented and passed 41 focused contract tests covering built-in docs, deterministic skill rendering, complete installs, idempotency, forward guards, AGENTS.md preservation, CLI validation, drift, and removed MCP inputs.
resolution: null
duplicate_of: null
---
Write test-first coverage for --docs, --skill, --install-skill, version pins, complete bundles, idempotency, target selection, forward-format guards, AGENTS.md preservation, and generated-copy drift.
