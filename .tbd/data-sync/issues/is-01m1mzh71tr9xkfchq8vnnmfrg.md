---
type: is
id: is-01m1mzh71tr9xkfchq8vnnmfrg
title: Print-only lines capture hover-only data
kind: task
status: closed
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-09-03-dt-design-system-refactor.md
labels: []
dependencies:
  - type: blocks
    target: is-01m1mzfd62sw8pgz3088tg4qcm
parent_id: is-01m1mzfbtbfjy3jn65xdyrfcn9
created_at: 2026-09-04T01:11:35.737Z
updated_at: 2026-09-04T01:17:05.448Z
closed_at: 2026-09-04T01:17:05.448Z
close_reason: "Implemented and verified: carry-over PDF reviewed page by page, print-width re-render confirmed, elements selection verified in rendered DOM, 100 tests green including updated goldens"
resolution: null
duplicate_of: null
---
Data that exists only in tooltips reaches the PDF as print-only lines: each concept entry prints its mention times as bracketed timestamps under the track, and its typed relations (e.g. 'leads to: Stargazer Lounge promotion') after the gloss, since graph edges print without their labels. Hidden on screen where dots and edge tooltips cover the same data.
