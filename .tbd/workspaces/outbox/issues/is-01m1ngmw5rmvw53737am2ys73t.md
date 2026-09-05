---
type: is
id: is-01m1ngmw5rmvw53737am2ys73t
title: Wrap the timeline into fixed-duration rows
kind: task
status: closed
priority: 0
version: 5
labels: []
dependencies:
  - type: blocks
    target: is-01m1ng5apmffpyrmqedmf8nk2v
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T06:10:41.463Z
updated_at: 2026-09-04T06:29:40.247Z
closed_at: 2026-09-04T06:29:40.246Z
close_reason: "Implemented in 65430b7 and verified on both exports: 11 half-hour rows on the 5.3-hour run with sections at 27.7 px median and 82 labels drawn, single unchanged row on the 22-min SNL example."
resolution: null
duplicate_of: null
---
The Timeline compresses the whole recording into one track. At 5.26 h that track is a
picket fence: nothing is readable and nothing is clickable.

MEASURED in the browser on the Lex #501 export (SVG track is 606 px wide, set by the
content column, regardless of window width):
  section band   194 rects, each 2 px wide
  speaker band   1,252 rects, 1-3 px wide
  frame dots     502 circles at 7 px diameter = 3,514 px of circles on a 606 px track,
                 so roughly 6x overlap, rendering as one continuous caterpillar
No section label can be drawn at 2 px, and a 2 px hover target is not usable.

FIX (user's design): break the recording into fixed-duration chunks — half an hour — and
wrap the chunks as rows, each row spanning the full track width.

The arithmetic at 606 px per row, 1800 s per row (0.337 px/s):
  rows            5.26 h -> 11 rows
  section         median 1.6 min = 96 s -> 32 px wide, up from 2 px (16x)
  speaker turn    median unit 13.6 s -> 4.6 px, up from 1-3 px
  frame dots      502 / 11 = ~46 per row, 7 px each = 322 px of 606 px, no overlap
32 px is enough for a real hover target and for short truncated labels.

Properties this design has, which is why it is the right one:
  - Short media is unchanged. A 22-min recording is one row of 30 min, i.e. exactly
    today's single track, so the SNL example does not move.
  - It degrades gracefully with length: 12 h is 24 rows, still one screen-ish, and px/s
    stays constant instead of shrinking with duration.
  - Absolute time stays readable — label each row with its own start (0:00, 0:30, 1:00).

Details to settle when implementing:
  - Row duration should adapt in coarse steps rather than being fixed at 30 min: keep one
    row for anything under it, and step up (30 min -> 1 h) past some row count so a 12 h
    recording does not become 24 rows. Choose the step so px/s never drops below the
    value that keeps a median section above ~20 px.
  - Sections spanning a row boundary get split into two rects; the hover and the
    highlight must still treat them as one section.
  - The per-concept tracks in the Concepts list use the same geometry and must wrap
    identically, or they stop aligning with the main timeline (the alignment the user
    asked for earlier).
  - Print: rows stack naturally, which is better for PDF than one compressed track.

## Notes

IMPLEMENTED in 65430b7. Measured in the browser on the real exports at the 606 px
content width.

Lex #501 (5.26 h) — before / after:
  rows                    1 / 11 half-hour rows
  section rects           194 at 2.0 px median / 204 at 27.7 px median (10 extra are
                          boundary splits)
  section labels drawn    0 / 82
  speaker rects           1,252 at 1-3 px / 2.2 px median
  frame dots per track    502 on one / 31-63 per row, no overlap
  axis                    row 0 reads 0:00 5:00 10:00 15:00 20:00 25:00; the last row
                          stops at the content end, 5:00:00 5:05:00 5:10:00 5:15:00

SNL (22 min) — unchanged, as intended:
  1 row, 7 sections, all 7 labelled, axis 0:00-4:00, 15 frame dots.

Reading marker verified across rows: exactly one visible at a time, and its row and x
match (floor(t/1800), (t mod 1800)/1800*606) at t = 0, 900, 1800, 5400, 11000, 18900.

Row duration ladder is 30 min -> 1 h -> 2 h, capped at 12 rows, with a single row
spanning the whole duration for anything under 30 min. So 12 h is 12 one-hour rows.

Settled differently from the plan: concept tracks stay single-row. They are
percentage-positioned bars showing where in the show a concept occurs, and the
alignment the user asked for was about sharing the panel's content width, which still
holds. Wrapping 24 of them into 11 rows each would have put 264 thin rows in the
Concepts panel.
