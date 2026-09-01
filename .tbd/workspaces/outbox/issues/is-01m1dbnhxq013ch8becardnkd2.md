---
type: is
id: is-01m1dbnhxq013ch8becardnkd2
title: Add the sticky timeline rail
kind: feature
status: closed
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-08-31-transcript-timeline-and-concept-map.md
labels: []
dependencies:
  - type: blocks
    target: is-01m1dbp0gq7rdk8vaaqfnag9s7
parent_id: is-01m1dbmypatm5c5e8sbhzqmphd
created_at: 2026-09-01T02:09:45.398Z
updated_at: 2026-09-01T05:54:01.406Z
closed_at: 2026-09-01T05:54:01.406Z
close_reason: Implemented and visually verified on the SNL five-speaker example in light and dark themes; print parity confirmed page-for-page against the committed PDF
resolution: null
duplicate_of: null
---
Add dt_rail.js.jinja: a fixed right-gutter rail mapping vertical position to media time. Lanes for the speaker band, section ticks, and frame ticks; a viewport window and a reading-center marker. Hover tooltip with time, speaker, and opening words; click to scroll; shift-click to seek via the existing openPopover. Keyboard focusable with arrow/Home/End navigation. Quantize the speaker band to rail pixel height so cost scales with rail height rather than transcript length. Reserve space above the YouTube popover and narrow when body.yt-open is set.
