---
type: is
id: is-01m1ng5apmffpyrmqedmf8nk2v
title: Cap frame capture density for long media
kind: task
status: open
priority: 1
version: 2
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T06:02:12.052Z
updated_at: 2026-09-04T06:10:56.551Z
---
Frame captures are emitted at paragraph granularity with only a similarity filter in
front of them. On long media that leaves far too many for one page.

MEASURED on Lex #501 (5.26 h):
  1,396 candidate timestamps -> 894 dropped as similar -> 502 kept, in 3.6 min.
  502 frames = 95 per hour; inter-frame gap median 18 s, min 0 s, max 403 s.
  The similarity filter already removed 64% and still left 502, so it cannot be the
  only control. Roughly 25 MB of images, each with a connector drawn to the timeline.

Extraction speed is not the problem — 3.6 min is fine. The problem is output volume: the
right-hand gutter becomes a continuous ribbon of thumbnails and the bundle gets heavy.

Add a density budget independent of the similarity filter, expressed so it is meaningful
at both ends of the range:
  - a minimum spacing (a frame no closer than N seconds to the previous kept frame), and
  - a total budget that scales sub-linearly with duration, so 22 min keeps what it keeps
    today and 5 h lands in the low hundreds at most.
  min gap of 0 s means duplicates at a single timestamp survive today; spacing fixes that.

Expose it as a flag so a user can ask for more. Keep the SNL example's frame set
unchanged — verify by diffing the regenerated example.

## Notes

CORRECTION to the earlier estimate: the frame assets are 115 MB, not ~25 MB.
  docs/watch_step09_normalize_timestamp_citations_1_8.doc.assets = 115 MB for 502 jpgs
  (~230 KB each). The whole workspace is 126 MB, so frames are 91% of it.

RENDERED DENSITY, measured in the browser: 502 circles at 7 px on a 606 px track is
3,514 px of marker on 606 px of space — about 6x overlap, drawn as one continuous
caterpillar rather than 502 markers.

Wrapping the timeline into rows (dt-1gl6) fixes the *overlap*: 502 / 11 rows = ~46 per
row, 7 px each on 606 px, which fits. It does not fix the other two costs — 115 MB of
assets in the bundle, and 502 thumbnails down the gutter of the transcript — so a
density cap is still wanted, just less urgently. Size the cap after dt-1gl6 lands so the
two decisions are made against the same rendering.
