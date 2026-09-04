---
type: is
id: is-01m1myprt55wb9ed0kcqbvzjre
title: Add the design-token enforcement test
kind: task
status: closed
priority: 2
version: 4
spec_path: docs/project/specs/active/plan-2026-09-03-dt-design-system-refactor.md
labels: []
dependencies:
  - type: blocks
    target: is-01m1myps42ckffx2crk8w1zscx
parent_id: is-01m1mypq8grvyy0afqzp9x491e
created_at: 2026-09-04T00:57:09.189Z
updated_at: 2026-09-04T01:08:34.401Z
closed_at: 2026-09-04T01:08:34.401Z
close_reason: "Consolidation complete: tokens file is the self-documenting source of truth, 8 enforcement tests green, regression pass clean"
resolution: null
duplicate_of: null
---
Python test fails on hex outside tokens, unsanctioned font-family declarations, radii besides the two tokens, or any title= attribute in dt modules.
