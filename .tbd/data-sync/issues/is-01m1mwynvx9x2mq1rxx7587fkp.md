---
type: is
id: is-01m1mwynvx9x2mq1rxx7587fkp
title: Slide the text column left to reserve the right rail area
kind: task
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-31-transcript-timeline-and-concept-map.md
labels: []
dependencies: []
created_at: 2026-09-04T00:26:31.154Z
updated_at: 2026-09-04T00:27:43.280Z
closed_at: 2026-09-04T00:27:43.280Z
close_reason: Implemented; layout verified at 1280 and 1500 widths on the SNL test bed with frames in the gutter and connectors intact
resolution: null
duplicate_of: null
---
The main column is no longer strictly centered once the dt views are active: from 1150px up it slides left (center minus 8rem, floored at 2rem, or at the TOC edge when a TOC is shown), leaving guaranteed room on the right for the frame gutter and the vertical rail. The frame gutter breakpoint drops from 1450px to 1150px and gutter images shrink to the space actually available. Narrow screens stay centered and untouched; print is unaffected.
