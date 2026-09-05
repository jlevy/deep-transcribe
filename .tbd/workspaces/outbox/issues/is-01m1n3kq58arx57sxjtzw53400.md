---
type: is
id: is-01m1n3kq58arx57sxjtzw53400
title: Validate and cap output scale for hours-long media
kind: task
status: closed
priority: 0
version: 6
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T02:22:52.071Z
updated_at: 2026-09-04T06:02:34.117Z
---
Unvalidated at scale because the run never reached processing. Expect: frame captures at paragraph granularity produce hundreds to thousands of ffmpeg seeks and a very large assets directory; the concept cap of 24 may be low for five hours; the Timeline overview must stay legible with dozens of sections; per-concept tracks and the rail need checking at that density; and the single HTML plus PDF may become impractically large. Measure each, then cap or tier what needs it.

## Notes

MEASURED on Lex #501 (5.26 h):

SECTIONS: 194 from insert_section_headings = one per 1.6 min (vs 23 YouTube chapters).
  Chunking: ~30-min chunks -> 11 chunks of ~18 sections; ~60-min -> 5 chunks of ~39.

WHOLE-DOC STAGES AT ~74k TOKENS — fine at this length, no context problem:
  add_transcript_outline      67 s
  add_transcript_description  13 s

FRAME CAPTURES: 1,396 timestamps -> 894 filtered as similar -> 502 kept, in 3.6 min.
  Extraction speed was NOT the problem (I predicted 25-45 min; it was 3.6).
  The problem is output volume: 502 frames in the gutter of one HTML page, roughly
  25 MB of images, with a connector drawn to each. Unusable as a page and heavy as a
  bundle. Needs a density cap for long media — frames per minute or a total budget —
  independent of the similarity filter, which already removed 64% and still left 502.
---

MEASURED, output pass (same run, exports/watch_step09_normalize_timestamp_citations_1_2.html):

PAGE WEIGHT — fine, not a blocker:
  html 1.51 MB total; JSON index island 0.50 MB (33% of page). No tiering needed.

SPEAKER ATTRIBUTION — correct at this length:
  Lex Fridman 11,424 w / 1:15:31 vs DHH 47,574 w / 4:00:14. Names resolved (not s0/s1),
  and the 4:1 split is right for an interview. 58,998 words, 1,396 units.

CONCEPTS — confirms the cap is far too low:
  24 concepts / 5.26 h = 4.6 per hour. On the 22-min SNL example the same cap gives
  ~65/h. Fix is dt-ucu8 (chunked extraction).

CONCEPT SPANS — a distinct bug, see the stray-mention bead:
  6 of 24 concepts span >15% of the recording; median span is 7 min, so the width comes
  from 1-2 outlier mentions each, not from genuinely recurring topics.

SECTIONS — the outline is the legibility problem, not the timeline:
  194 sections, median 260 words, p10 128, p90 580; 60 sections under 200 words.
  The Outline view renders one line per section, so a 194-line list with no hierarchy.

FRAMES — cap still needed:
  502 frames = 95/hour; inter-frame gap median 18 s, min 0 s (duplicates at one
  timestamp), max 403 s.

This bead's validation work is done; the fixes are split out as separate beads.
