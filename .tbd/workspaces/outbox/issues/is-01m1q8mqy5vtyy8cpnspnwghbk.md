---
type: is
id: is-01m1q8mqy5vtyy8cpnspnwghbk
title: Make the rerun table in docs.md true
kind: task
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-09-04-long-form-stabilization.md
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T22:29:17.380Z
updated_at: 2026-09-05T00:07:22.673Z
closed_at: 2026-09-04T22:42:11.971Z
close_reason: Row rewritten to the measured cost of a hint change; 12-hour line now names 5h15m as the verified limit and twelve hours as the design target.
resolution: null
duplicate_of: null
---
docs.md row 162 says a hint change 'reuses the cached transcript and everything through section headings'. Measured on a fresh workspace it re-runs break_into_paragraphs and insert_section_headings — 46 minutes on #501 — because hints are written back to the hashed resource (see dt-xjlp). Rewrite the row to what is measured now; when dt-xjlp lands, restore the original wording. Same pass: soften line 62's '12 hours or more is supported' to 'tested end to end at five hours' until dt-qc7j Phase 3 produces a real 12-hour run. Do this AFTER the R6 and R8 review fixes land, since both also edit docs.md.

## Notes

Row 162 will be refined once the at-scale edit run lands: two cases — first application of hints re-runs paragraphs and section headings (~46 min at five hours); editing an existing hint resumes at the outline.
