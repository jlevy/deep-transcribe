---
type: is
id: is-01m1ng4k98ct0rh0aez0f65mq1
title: Drop stray concept mentions that inflate spans
kind: bug
status: closed
priority: 1
version: 2
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T06:01:48.071Z
updated_at: 2026-09-04T06:34:47.717Z
closed_at: 2026-09-04T06:34:47.716Z
close_reason: "Fixed in 196226e. A mention must land on a unit of at least three words: drops all eight one-word acknowledgments on the 5.3-hour run, empties no concept, median span 6.9 -> 4.5 min, spans over 15% of the recording 6 -> 4. The four that remain are genuine recurrences, split out as a rendering bead."
resolution: null
duplicate_of: null
---
Concept mentions include far-flung outliers that land on filler and stretch a concept's
span across most of the recording. The topic timeline bar and the concept's [start-end]
label then describe the whole show instead of where the idea actually lives.

MEASURED on Lex #501 (5.26 h, 24 concepts, 66 mention gaps):
  6 of 24 concepts span >15% of the recording, but the median span is only 7 min — the
  width comes from one or two outliers, not from genuine recurrence.
  9 mention gaps exceed 20 min; 5 exceed 60 min.

The outliers resolve to acknowledgment units:
  "AI's superhuman vulnerability-finding"  0:14:12-3:33:43 (63% of the recording)
      real mention @0:14:12, then @3:33:41 "But the road there is pretty rocky."
  "Linux's config-file/CLI nature suits agents"  1:40:59-3:40:04
      two real mentions at 1:40-1:41, then @3:39:58 "Mhmm."
  "Omarchy Linux distribution"  0:39:26-1:49:02
      three real mentions at 0:39, then @1:48:57 "Mhmm."
  "Stoicism and Amor Fati"  1:09:31-3:15:52
      two real at 1:09-1:10, then @3:14:37 "Yeah."

Two independent causes, both worth fixing:
  1. A mention may resolve to a unit with no substance. Require the resolved unit to
     carry content — drop mentions landing on units below a small word count, or on
     units that are pure acknowledgment.
  2. Even on a real unit, a lone mention an hour from the concept's cluster should not
     define the span. Cluster the mentions and either drop isolated outliers or report
     the span from the dominant cluster while keeping the mention markers.

Fix in _resolve_concepts() in src/deep_transcribe/transcript_index.py, which builds
mentions and span. Check the SNL example does not regress (short media has no long gaps,
so the pruning should be a no-op there).
