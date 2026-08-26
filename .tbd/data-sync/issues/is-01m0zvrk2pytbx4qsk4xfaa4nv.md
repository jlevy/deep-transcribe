---
type: is
id: is-01m0zvrk2pytbx4qsk4xfaa4nv
title: Add high-quality browser PDF export
kind: feature
status: in_progress
priority: 1
version: 5
labels: []
dependencies: []
parent_id: is-01m0zpq37wdhx51829qx0xmf0t
child_order_hints:
  - is-01m0zw7p1cq8607eb675yape5m
created_at: 2026-08-26T20:21:40.053Z
updated_at: 2026-08-26T23:37:09.584Z
---
Evaluate existing Kash PDF conversion against standards-based browser print output, define a clean DeepTranscribe export path, preserve print CSS and typography, and verify generated PDFs visually. Keep private acceptance fixtures outside repository records.

## Notes

Acceptance comparison favors printing completed Deep Transcribe HTML with a Chromium-class browser. Browser output preserves title, serif/sans typography, print CSS, project attribution, frame layout, Letter page size, embedded fonts, searchable text, and tagged-PDF structure. Existing Kash create_pdf rewraps the body, scales content, defaults to A4, replaces project attribution, loses the title, emits an untagged PDF, and depends on an unavailable WeasyPrint/native-library stack. The validated acceptance PDF is 84 Letter pages, contains all 120 frames, uses matching 8pt light-gray sans-serif for timestamps and attribution, and has no frame nested inside timestamp brackets or trailing timestamp gap. Remaining work: expose this browser-backed export as a built-in deterministic CLI workflow with browser discovery, stable naming, asset resolution, and clear failure guidance.
