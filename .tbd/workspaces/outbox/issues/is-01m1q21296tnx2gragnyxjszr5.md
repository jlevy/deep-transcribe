---
type: is
id: is-01m1q21296tnx2gragnyxjszr5
title: "PR #19 review R10: per-theme graphs do not re-lay on resize; cleanup unreachable"
kind: bug
status: closed
priority: 2
version: 3
spec_path: docs/project/specs/active/plan-2026-09-04-long-form-stabilization.md
labels: []
dependencies: []
parent_id: is-01m1q1zs4f81krjzenfbtmp35t
created_at: 2026-09-04T20:33:41.158Z
updated_at: 2026-09-04T22:44:34.652Z
closed_at: 2026-09-04T22:44:34.651Z
close_reason: "Per-theme graphs re-lay via the existing ResizeObserver, collapsed groups lay out on expand, and the failure cleanup is now reachable (the catch tested a variable assigned last in the try). Verified in real headless Chrome: 5/5 resize cases, 4/4 forced-failure cases."
resolution: null
duplicate_of: null
---
dt_concepts.js.jinja — layoutGraph runs once, so chip positions are wrong after a window resize; and the error-path cleanup is unreachable. Re-lay on resize (debounced) and make the cleanup reachable.
