---
type: is
id: is-01m1qdyhhry2322zwqx0dsscr2
title: Collapse a hint span as one block, not one fragment per section
kind: bug
status: open
priority: 1
version: 1
spec_path: docs/project/specs/active/plan-2026-09-04-long-form-stabilization.md
labels: []
dependencies: []
parent_id: is-01m1n3q978x6fyhsyfm175ngy6
created_at: 2026-09-05T00:02:01.399Z
updated_at: 2026-09-05T00:02:01.399Z
---
Measured on the full 5h15m export with the current code. The stored teaser hint is one span, 0:00:05 - 0:01:49, six paragraphs. The transcript shows FOUR collapsed blocks — 2, 2, 1 and 1 paragraphs — each headed 'Teaser — 0 min, left out of the analysis' (20-30 s rounds to 0 min), because collapseSegments in dt_core.js.jinja splits a run on unit.section and four section headings were inserted inside the highlight clip. The reader sees four tiny boxes instead of one 'Teaser — 2 min' box, and three of the four pulled a section heading inside them (R4's rule fires because each fragment does reach its own section's end).

Fix: collapse the contiguous suppressed span as ONE block regardless of section boundaries; any h2 that falls entirely inside the span goes inside the block (they head only suppressed material); an h2 whose section continues past the span stays out (R4). Label durations under a minute in seconds. Test with the real shape: six units over 104 s spanning four sections, expect one block, one head reading about 2 min, all four inner h2s inside. Verify in a browser on the full export — a re-export is cheap now that every stage is cached.
