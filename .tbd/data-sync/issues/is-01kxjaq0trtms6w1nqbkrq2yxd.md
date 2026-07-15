---
type: is
id: is-01kxjaq0trtms6w1nqbkrq2yxd
title: Add automated portability checks for transcript exports
kind: task
status: open
priority: 2
version: 1
labels:
  - html
  - testing
dependencies: []
parent_id: is-01kxj4xxyfwmxmk3z9mebcf92x
created_at: 2026-07-15T07:26:29.719Z
updated_at: 2026-07-15T07:26:29.719Z
---
Test the rendered artifact graph rather than only HTML creation: fail on load-bearing external scripts, styles, fonts, or missing relative images; verify every bundled asset exists; verify the single-file variant has no required siblings; and cover exports with and without frame captures.
