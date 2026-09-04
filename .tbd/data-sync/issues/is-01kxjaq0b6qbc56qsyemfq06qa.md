---
type: is
id: is-01kxjaq0b6qbc56qsyemfq06qa
title: Add portable transcript HTML and ZIP bundle exports
kind: feature
status: open
priority: 1
version: 3
labels:
  - html
  - portability
dependencies: []
parent_id: is-01m1n2x04sy0v4w4t2jgpf7msp
created_at: 2026-07-15T07:26:29.221Z
updated_at: 2026-09-04T02:10:28.149Z
---
VERIFIED FEASIBLE (audit 2026-09-03 against a real minified export): a single-file standalone HTML is a small, tractable change. Tailwind is ALREADY compiled and inlined by the minify step. What remains load-bearing: six woff2 faces from cdn.jsdelivr fontsource, the feather-icons script, Google Fonts preconnects, the YouTube thumbnail, and the local .assets frame captures. Inline the fonts as base64 (or fall back to a system stack), replace feather with inline SVG for the handful of icons used, and inline the thumbnail and frames as data URIs. YouTube embed and timestamp links stay external by design — that is the video itself. Estimated single-file size for a short piece is ~1-2 MB; long transcripts with many frames argue for the ZIP bundle variant as the alternative. Ship behind a flag (e.g. --standalone) alongside the existing --elements.
