---
type: is
id: is-01m12k2d0v1agkrwgs21dtnxs9
title: Release kash-media v0.4.8 with the YouTube discovery mapping
kind: task
status: open
priority: 1
version: 2
labels: []
dependencies:
  - type: blocks
    target: is-01m12k2db1dqxc18fmmsjcy70x
parent_id: is-01m1118hwdhra16fmaz6jd1smt
created_at: 2026-08-27T21:47:27.642Z
updated_at: 2026-08-27T21:47:27.968Z
---
On jlevy/kash-media#11 (draft), after kash-shell 0.4.10 publishes:

1. uv lock --upgrade-package kash-shell
2. Confirm CI is green — the 4 reportCallIssue errors are only the missing MediaMetadata fields
3. Undraft, merge, tag v0.4.8

The direct kash-shell>=0.4.10,<0.5 floor is already committed on the branch. kash-docs needs no release: 0.2.7 already allows kash-shell >=0.4.9,<0.5.

Current: kash-media v0.4.7.
