---
type: is
id: is-01m0yh588tby44g9tdcv5djhkb
title: Make skill runner selection reject stale executables
kind: bug
status: in_progress
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-08-26-self-documenting-skill.md
labels: []
dependencies: []
parent_id: is-01m0yf48parshvzra5k25xv9wr
created_at: 2026-08-26T07:57:06.201Z
updated_at: 2026-08-26T07:57:15.094Z
---
The installed skill says to prefer any deep-transcribe found on PATH. A stale v0.1.9 executable was selected in the development checkout and rejected --docs even though the repository provides v0.1.11 through uv run. Add a tested repository-runner preference and a capability/version check before accepting a PATH executable, then regenerate every skill surface and validate the real commands.
