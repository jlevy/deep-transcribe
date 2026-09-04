---
type: is
id: is-01m1mzfbtbfjy3jn65xdyrfcn9
title: Print carry-over for the analysis views
kind: epic
status: closed
priority: 1
version: 8
spec_path: docs/project/specs/active/plan-2026-09-03-dt-design-system-refactor.md
labels: []
dependencies: []
child_order_hints:
  - is-01m1mzfc4fyp2d4g746ebmz4dm
  - is-01m1mzfcf7v14svd75h2jkp5x3
  - is-01m1mzfctwc9qdrs3es7b35dfk
  - is-01m1mzfd62sw8pgz3088tg4qcm
  - is-01m1mzh71tr9xkfchq8vnnmfrg
  - is-01m1mzh7dbzepcqj1cgspdn6hj
created_at: 2026-09-04T01:10:35.081Z
updated_at: 2026-09-04T01:17:05.757Z
closed_at: 2026-09-04T01:17:05.756Z
close_reason: Print carry-over epic complete in one pass
resolution: null
duplicate_of: null
---
Replace hide-everything printing with a systematic carry-over: static, data-bearing views (headings, Summary, Timeline overview, Speakers table, outline chips, Concepts with tracks and graph, Claims, prose styling) print; viewport-bound interactive chrome (rail, connectors, tooltips, reading marker, gutter placement, selection states) is held out, with the same data reaching the PDF through the panels. The old byte-parity contract is deliberately superseded.
