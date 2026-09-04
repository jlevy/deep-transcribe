---
type: is
id: is-01m1q20zsktpyf6ae9cdwjc0q2
title: "PR #19 review R4: collapsed segment steals the section heading"
kind: bug
status: closed
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-09-04-long-form-stabilization.md
labels: []
dependencies: []
parent_id: is-01m1q1zs4f81krjzenfbtmp35t
created_at: 2026-09-04T20:33:38.609Z
updated_at: 2026-09-04T22:29:16.046Z
closed_at: 2026-09-04T20:46:39.943Z
close_reason: Heading now moves only when the suppressed run reaches the section's end.
resolution: null
duplicate_of: null
---
MAJOR. collapseSegments moves an immediately preceding h2 into the collapsed body, but a suppressed run usually covers only the FIRST paragraphs of a section, so the heading is pulled in and the section's remaining un-suppressed paragraphs are stranded headingless — the inverse of what ed8ad52 fixed. dt_core.js.jinja:96. Fix: only move the heading when the collapsed run covers the whole section.
