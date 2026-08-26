---
type: is
id: is-01m0yh588tby44g9tdcv5djhkb
title: Make skill runner selection reject stale executables
kind: bug
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-26-self-documenting-skill.md
labels: []
dependencies: []
parent_id: is-01m0yf48parshvzra5k25xv9wr
created_at: 2026-08-26T07:57:06.201Z
updated_at: 2026-08-26T08:39:49.270Z
closed_at: 2026-08-26T08:39:49.243Z
close_reason: "Implemented stale-runner rejection in PR #12 with TDD, regenerated f02 skill surfaces, built-artifact smoke tests, private cache-aware end-to-end validation, and passing CI."
resolution: null
duplicate_of: null
---
The installed skill says to prefer any deep-transcribe found on PATH. A stale v0.1.9 executable was selected in the development checkout and rejected --docs even though the repository provides v0.1.11 through uv run. Add a tested repository-runner preference and a capability/version check before accepting a PATH executable, then regenerate every skill surface and validate the real commands.
