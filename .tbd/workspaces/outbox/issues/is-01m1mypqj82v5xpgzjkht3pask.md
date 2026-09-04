---
type: is
id: is-01m1mypqj82v5xpgzjkht3pask
title: Extract dt_tokens.css.jinja
kind: task
status: closed
priority: 2
version: 5
spec_path: docs/project/specs/active/plan-2026-09-03-dt-design-system-refactor.md
labels: []
dependencies:
  - type: blocks
    target: is-01m1mypqwasr8bz6j96qevz1vt
  - type: blocks
    target: is-01m1myprt55wb9ed0kcqbvzjre
parent_id: is-01m1mypq8grvyy0afqzp9x491e
created_at: 2026-09-04T00:57:07.911Z
updated_at: 2026-09-04T01:08:34.345Z
closed_at: 2026-09-04T01:08:34.344Z
close_reason: "Consolidation complete: tokens file is the self-documenting source of truth, 8 enforcement tests green, regression pass clean"
resolution: null
duplicate_of: null
---
Move all tokens (palette, kind colors, text roles, radii, spacing) into a dedicated tokens partial with the design documentation as comments, imported first.
