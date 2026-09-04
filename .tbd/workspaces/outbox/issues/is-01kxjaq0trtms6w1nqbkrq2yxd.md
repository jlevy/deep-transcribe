---
type: is
id: is-01kxjaq0trtms6w1nqbkrq2yxd
title: Add automated portability checks for transcript exports
kind: task
status: open
priority: 1
version: 3
labels:
  - html
  - testing
dependencies: []
parent_id: is-01m1n2x04sy0v4w4t2jgpf7msp
created_at: 2026-07-15T07:26:29.719Z
updated_at: 2026-09-04T02:10:28.969Z
---
Test the rendered artifact graph rather than only HTML creation: fail on load-bearing external scripts, styles, fonts, or missing relative images; verify every bundled asset exists; verify the single-file variant has no required siblings; and cover exports with and without frame captures.
