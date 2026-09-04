---
type: is
id: is-01m1q212jf1rpbkeeyetz96gb7
title: "PR #19 review R11: a suggestion the user already adopted is re-offered"
kind: bug
status: closed
priority: 2
version: 3
spec_path: docs/project/specs/active/plan-2026-09-04-long-form-stabilization.md
labels: []
dependencies: []
parent_id: is-01m1q1zs4f81krjzenfbtmp35t
created_at: 2026-09-04T20:33:41.454Z
updated_at: 2026-09-04T22:43:36.484Z
closed_at: 2026-09-04T22:43:36.483Z
close_reason: A detected clip already covered by a hint in effect (item-carried or caller-supplied, 3 s tolerance) is logged and not re-offered. Tests drive _process_transcript; verified to fail on revert.
resolution: null
duplicate_of: null
---
detect_segments re-emits segments.suggested.yml including spans already present in the hints file passed via --segments, so the user is asked again to adopt what they adopted. Filter suggestions against the hints already in effect.
