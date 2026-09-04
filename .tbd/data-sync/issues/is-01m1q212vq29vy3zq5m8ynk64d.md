---
type: is
id: is-01m1q212vq29vy3zq5m8ynk64d
title: "PR #19 review R12: exclusion tests assert on an argument production never passes"
kind: bug
status: open
priority: 1
version: 1
labels: []
dependencies: []
parent_id: is-01m1q1zs4f81krjzenfbtmp35t
created_at: 2026-09-04T20:33:41.751Z
updated_at: 2026-09-04T20:33:41.751Z
---
The tests for suppression call split_body(hints=...) / drop_suppressed directly — the argument no production caller supplies — so they pass while the feature is inert. This is the test-quality half of R1: rewrite them to drive the actions.
