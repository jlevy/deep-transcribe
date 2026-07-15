---
type: is
id: is-01kxjaq0b6qbc56qsyemfq06qa
title: Add portable transcript HTML and ZIP bundle exports
kind: feature
status: open
priority: 2
version: 1
labels:
  - html
  - portability
dependencies: []
parent_id: is-01kxj4xxyfwmxmk3z9mebcf92x
created_at: 2026-07-15T07:26:29.221Z
updated_at: 2026-07-15T07:26:29.221Z
---
Provide an explicitly portable export path. A single-file variant should inline or otherwise eliminate required sibling assets within a practical size limit; large exports should fall back to or additionally produce a ZIP bundle with a clear HTML entry point. Do not embed the original source media by default. Define behavior for frame compression, size thresholds, and offline timestamp links.
