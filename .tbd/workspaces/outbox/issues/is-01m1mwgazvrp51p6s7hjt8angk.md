---
type: is
id: is-01m1mwgazvrp51p6s7hjt8angk
title: Timestamp chips jump to the video, tolerating no video
kind: task
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-31-transcript-timeline-and-concept-map.md
labels: []
dependencies: []
created_at: 2026-09-04T00:18:41.273Z
updated_at: 2026-09-04T00:20:04.870Z
closed_at: 2026-09-04T00:20:04.870Z
close_reason: Implemented and verified on the SNL test bed; timeline type at design-system sizes confirmed by capture
resolution: null
duplicate_of: null
---
Clicking a timestamp chip (outline sections, claims) opens the video at that time via the existing playAt bridge instead of scrolling. playAt already degrades: no linkable video (local media, non-YouTube source, stripped file links) falls back to scrolling the transcript, and on file:// pages links open YouTube directly.
