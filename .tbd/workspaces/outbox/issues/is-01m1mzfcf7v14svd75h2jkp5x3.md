---
type: is
id: is-01m1mzfcf7v14svd75h2jkp5x3
title: Restructure print CSS from blanket-hide to carry-over
kind: task
status: closed
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-09-03-dt-design-system-refactor.md
labels: []
dependencies:
  - type: blocks
    target: is-01m1mzfctwc9qdrs3es7b35dfk
  - type: blocks
    target: is-01m1mzfd62sw8pgz3088tg4qcm
parent_id: is-01m1mzfbtbfjy3jn65xdyrfcn9
created_at: 2026-09-04T01:10:35.750Z
updated_at: 2026-09-04T01:17:05.420Z
closed_at: 2026-09-04T01:17:05.420Z
close_reason: "Implemented and verified: carry-over PDF reviewed page by page, print-width re-render confirmed, elements selection verified in rendered DOM, 100 tests green including updated goldens"
resolution: null
duplicate_of: null
---
Drop the blanket .dt-ui hide and the label/leading print resets; hold out only the rail, connectors, tooltips, and reading marker; neutralize selection/dim/mention states; add break-inside protection for panels, tables, charts, and entries; force color printing on color-bearing fills.
