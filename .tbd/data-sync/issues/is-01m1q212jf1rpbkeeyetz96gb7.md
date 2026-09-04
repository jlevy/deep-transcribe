---
type: is
id: is-01m1q212jf1rpbkeeyetz96gb7
title: "PR #19 review R11: a suggestion the user already adopted is re-offered"
kind: bug
status: open
priority: 2
version: 2
spec_path: docs/project/specs/active/plan-2026-09-04-long-form-stabilization.md
labels: []
dependencies: []
parent_id: is-01m1q1zs4f81krjzenfbtmp35t
created_at: 2026-09-04T20:33:41.454Z
updated_at: 2026-09-04T22:29:16.046Z
---
detect_segments re-emits segments.suggested.yml including spans already present in the hints file passed via --segments, so the user is asked again to adopt what they adopted. Filter suggestions against the hints already in effect.
