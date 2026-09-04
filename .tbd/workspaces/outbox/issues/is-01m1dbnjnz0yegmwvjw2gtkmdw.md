---
type: is
id: is-01m1dbnjnz0yegmwvjw2gtkmdw
title: Connect frame captures to the timeline
kind: feature
status: closed
priority: 2
version: 4
spec_path: docs/project/specs/active/plan-2026-08-31-transcript-timeline-and-concept-map.md
labels: []
dependencies:
  - type: blocks
    target: is-01m1dbnk0wazn3pteq5k08jppx
parent_id: is-01m1dbmypatm5c5e8sbhzqmphd
created_at: 2026-09-01T02:09:46.174Z
updated_at: 2026-09-01T05:54:01.420Z
closed_at: 2026-09-01T05:54:01.420Z
close_reason: Implemented and visually verified on the SNL five-speaker example in light and dark themes; print parity confirmed page-for-page against the committed PDF
resolution: null
duplicate_of: null
---
Add dt_frames.js.jinja: on wide viewports move frame captures into a right-hand gutter and draw a single-stroke cubic bezier from each image to its rail tick. Draw only for frames intersecting the viewport via IntersectionObserver. Hovering an image brightens its connector and highlights its tick; hovering the tick outlines the image. Below the gutter breakpoint and in print, frames stay inline exactly as today with no connectors.
