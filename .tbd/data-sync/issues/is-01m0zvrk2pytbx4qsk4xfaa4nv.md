---
type: is
id: is-01m0zvrk2pytbx4qsk4xfaa4nv
title: Add high-quality browser PDF export
kind: feature
status: in_progress
priority: 1
version: 4
labels: []
dependencies: []
parent_id: is-01m0zpq37wdhx51829qx0xmf0t
child_order_hints:
  - is-01m0zw7p1cq8607eb675yape5m
created_at: 2026-08-26T20:21:40.053Z
updated_at: 2026-08-26T20:29:55.301Z
---
Evaluate existing Kash PDF conversion against standards-based browser print output, define a clean DeepTranscribe export path, preserve print CSS and typography, and verify generated PDFs visually. Keep private acceptance fixtures outside repository records.

## Notes

Acceptance comparison favors printing the completed DeepTranscribe HTML with a Chromium-class browser. Browser output preserved the title, intended serif/sans typography, print CSS, project attribution, frame layout, Letter page size, embedded fonts, searchable text, and tagged-PDF structure. Existing Kash create_pdf rewraps the body, applies transform scale(0.9), defaults to A4, replaces project attribution, loses the document title, emits an untagged PDF, and requires an optional WeasyPrint/native-library stack that was unavailable in the DeepTranscribe environment. WeasyPrint also rejected several CSS and variable-font features. Recommended implementation: optional browser-backed PDF export after HTML generation, deterministic browser discovery, explicit print background/page settings, automatic asset resolution, stable output naming, and Poppler visual QA.
