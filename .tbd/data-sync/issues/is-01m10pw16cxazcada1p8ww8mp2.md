---
type: is
id: is-01m10pw16cxazcada1p8ww8mp2
title: Keep transcript turns intact across printed pages
kind: bug
status: closed
priority: 1
version: 4
labels: []
dependencies: []
parent_id: is-01m10kjrzedwht5b4mqbmwm3yp
created_at: 2026-08-27T04:15:24.363Z
updated_at: 2026-08-27T04:21:18.926Z
closed_at: 2026-08-27T04:21:18.925Z
close_reason: No clipped turns or frames remain in the final Chrome PDF.
resolution: null
duplicate_of: null
---
Chrome can fragment a transcript paragraph at a page boundary after timestamp sizing changes, clipping the start of the continuation. Keep ordinary transcript turns intact when they fit on a page and visually validate the browser PDF.

## Notes

During seven-page PDF QA, Chrome clipped a frame-bearing transcript turn at a page boundary. Added a print-only guard that keeps paragraphs containing frame captures intact while allowing ordinary long paragraphs to flow across pages. Visually rechecked all seven final pages.
