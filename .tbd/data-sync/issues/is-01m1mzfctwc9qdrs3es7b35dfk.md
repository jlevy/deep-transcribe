---
type: is
id: is-01m1mzfctwc9qdrs3es7b35dfk
title: Re-render charts at print width
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
created_at: 2026-09-04T01:10:36.123Z
updated_at: 2026-09-04T01:17:05.438Z
closed_at: 2026-09-04T01:17:05.438Z
close_reason: "Implemented and verified: carry-over PDF reviewed page by page, print-width re-render confirmed, elements selection verified in rendered DOM, 100 tests green including updated goldens"
resolution: null
duplicate_of: null
---
beforeprint/afterprint in the core dispatches a print-mode event with the --dt-print-width token; the Timeline overview and concept graph re-render at that width so type prints at full size instead of scaling down, and restore afterward.
