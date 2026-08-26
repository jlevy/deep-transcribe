---
type: is
id: is-01m0yf4vy1d0bt0e8zpz8yjh33
title: Remove the MCP server as a hard cut
kind: task
status: closed
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-26-self-documenting-skill.md
delegate: codex@spud10.local
labels:
  - cli
dependencies:
  - type: blocks
    target: is-01m0yf4wbyqyw7g1kr9775qv0x
  - type: blocks
    target: is-01m0yf4wq1tesb7t6kq0pabd67
parent_id: is-01m0yf48parshvzra5k25xv9wr
hold: null
hold_until: null
created_at: 2026-08-26T07:21:56.416Z
updated_at: 2026-08-26T07:53:07.425Z
started_at: 2026-08-26T07:34:39.285Z
closed_at: 2026-08-26T07:34:39.560Z
close_reason: Deleted MCP and logs subcommands, legacy server flags, MCP runtime imports and dispatch, and mcp_tool action exports; removed user-facing MCP documentation with no compatibility shim.
resolution: null
duplicate_of: null
---
Delete MCP and logs subcommands, compatibility flags, server runner code, dispatch paths, MCP action annotations, tests, and documentation references with no shims.
