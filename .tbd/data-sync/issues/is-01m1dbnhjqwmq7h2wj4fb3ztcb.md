---
type: is
id: is-01m1dbnhjqwmq7h2wj4fb3ztcb
title: Add the client core module and visualization stylesheet
kind: task
status: open
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-31-transcript-timeline-and-concept-map.md
labels: []
dependencies:
  - type: blocks
    target: is-01m1dbnhxq013ch8becardnkd2
  - type: blocks
    target: is-01m1dbnjb917373qah962kjcqc
  - type: blocks
    target: is-01m1dbnjnz0yegmwvjw2gtkmdw
parent_id: is-01m1dbmypatm5c5e8sbhzqmphd
created_at: 2026-09-01T02:09:45.046Z
updated_at: 2026-09-01T02:10:31.535Z
---
Add dt_core.js.jinja (index parsing, DOM binding by citation key, time-to-pixel math, the CustomEvent contract, and a no-op path when the index is absent) and dt_viz.css.jinja (the eight-hue speaker palette with light and dark variants as CSS custom properties, plus print rules hiding all interactive chrome). Every foreground variant must clear WCAG AA against both background values.
