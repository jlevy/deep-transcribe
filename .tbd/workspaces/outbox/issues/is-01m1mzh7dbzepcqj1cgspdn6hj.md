---
type: is
id: is-01m1mzh7dbzepcqj1cgspdn6hj
title: Add --elements to choose page parts
kind: feature
status: closed
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-09-03-dt-design-system-refactor.md
labels: []
dependencies:
  - type: blocks
    target: is-01m1mzfd62sw8pgz3088tg4qcm
parent_id: is-01m1mzfbtbfjy3jn65xdyrfcn9
created_at: 2026-09-04T01:11:36.105Z
updated_at: 2026-09-04T01:17:05.456Z
closed_at: 2026-09-04T01:17:05.456Z
close_reason: "Implemented and verified: carry-over PDF reviewed page by page, print-width re-render confirmed, elements selection verified in rendered DOM, 100 tests green including updated goldens"
resolution: null
duplicate_of: null
---
A comma-separated --elements flag selects which parts the HTML export includes: title, thumbnail, summary, timeline, speakers, outline, concepts, claims, frames, transcript. Default is everything. Implemented as a config injected into the exported page; the client skips excluded panels and hides excluded server-rendered parts, so one pipeline run can produce differently scoped exports.
