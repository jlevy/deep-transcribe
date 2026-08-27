---
type: is
id: is-01m10nen5agg9ebbaar5ezemr0
title: Document portable browser PDF export
kind: task
status: in_progress
priority: 1
version: 3
labels: []
dependencies: []
parent_id: is-01m10kjrzedwht5b4mqbmwm3yp
created_at: 2026-08-27T03:50:37.481Z
updated_at: 2026-08-27T03:56:08.640Z
---
Document the supported Print to PDF workflow for Deep Transcribe's self-contained HTML, including an ordinary browser path and a reproducible Chrome or Chromium command for agent automation. Validate that the untouched hotel HTML prints correctly without renderer-specific CSS or bundled PDF dependencies.

## Notes

Added portable Print to PDF instructions to the packaged --docs guide, a concise note beside the README sample, and browser-print checks to the E2E runbook. The documented path uses an ordinary browser and adds no renderer dependency. Lint, 60 tests, Flowmark, and diff checks pass.
