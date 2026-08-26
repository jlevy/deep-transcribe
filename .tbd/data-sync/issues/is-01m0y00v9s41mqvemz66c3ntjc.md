---
type: is
id: is-01m0y00v9s41mqvemz66c3ntjc
title: Make metadata-only reruns explicit and regression-tested
kind: feature
status: closed
priority: 1
version: 5
labels: []
dependencies: []
parent_id: is-01m0xwzrh7debayb7dhcrz1d9y
created_at: 2026-08-26T02:57:36.054Z
updated_at: 2026-08-26T03:46:08.990Z
closed_at: 2026-08-26T03:46:08.990Z
close_reason: Implemented, regression-tested, and validated with real private and public end-to-end workflows.
resolution: null
duplicate_of: null
---
Audit rerun/cache boundaries and add tests so added context or speaker metadata can redo downstream features without repeating speech-to-text or media work.

## Notes

Validated the public hotel workflow from a fresh basic transcript through an annotated context-only rerun without force flags. The rerun logged a raw transcript cache hit, kept one Deepgram request, applied exact role labels, and rendered all 19 frame captures.
