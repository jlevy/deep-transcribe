---
type: is
id: is-01m1q21296tnx2gragnyxjszr5
title: "PR #19 review R10: per-theme graphs do not re-lay on resize; cleanup unreachable"
kind: bug
status: open
priority: 2
version: 1
labels: []
dependencies: []
parent_id: is-01m1q1zs4f81krjzenfbtmp35t
created_at: 2026-09-04T20:33:41.158Z
updated_at: 2026-09-04T20:33:41.158Z
---
dt_concepts.js.jinja — layoutGraph runs once, so chip positions are wrong after a window resize; and the error-path cleanup is unreachable. Re-lay on resize (debounced) and make the cleanup reachable.
