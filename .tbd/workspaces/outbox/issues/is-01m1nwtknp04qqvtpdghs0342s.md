---
type: is
id: is-01m1nwtknp04qqvtpdghs0342s
title: Short-media regression check for the long-form work
kind: task
status: closed
priority: 3
version: 3
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T09:43:32.243Z
updated_at: 2026-09-04T09:43:36.582Z
closed_at: 2026-09-04T09:43:36.581Z
close_reason: "Verified in a browser: all six guards fired correctly at once on the re-rendered SNL example."
resolution: null
duplicate_of: null
---
Verification record, kept because the numbers are the evidence that the long-form changes did not disturb short media.

## Notes

SHORT-MEDIA REGRESSION CHECK, run in a browser against the SNL example re-rendered with
every change from this branch (2026-09-04 02:45). Every "short media is untouched" claim
made during this work, verified rather than asserted:

  timeline rows              1        single unwrapped track, as before
  concept theme groups       0        no themes on short media, so no grouping
  outline theme groups       0        outline stays flat under 30 entries
  per-theme graphs           0        the single global graph is drawn instead
  global graphs              1
  suppressed segments        0        no hints, no collapsing
  frames                     15       under the 45/hour cap, so untouched
  broken frames              0        the asset relocation fix works here too
  timeline sections/labels   7 / 7    every section still labelled
  concepts                   24
  axis                       0:00 1:00 2:00 3:00 4:00

Each of these is a different guard: FLAT_LIST_LIMIT, OUTLINE_FLAT_LIMIT, the perTheme
condition, chooseRows's single-row case, the frame density target, and the hints being
absent. All of them fired correctly at once, which is the case that matters — they were
written separately and had never been exercised together.
