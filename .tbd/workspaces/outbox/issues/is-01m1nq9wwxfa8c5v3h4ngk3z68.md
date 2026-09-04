---
type: is
id: is-01m1nq9wwxfa8c5v3h4ngk3z68
title: Keep hint reruns cheap and prove it
kind: task
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-09-04-transcript-segments.md
labels: []
dependencies: []
parent_id: is-01m1n3q978x6fyhsyfm175ngy6
created_at: 2026-09-04T08:07:01.788Z
updated_at: 2026-09-04T18:27:41.676Z
closed_at: 2026-09-04T18:27:41.675Z
close_reason: "Both properties measured: an unchanged rerun costs 4 s with zero API calls, and adding a hint costs 48 s and 3 LLM calls while leaving speech-to-text, speaker correction, paragraphs and section headings untouched."
resolution: null
duplicate_of: null
---
The hint loop only works if rerunning with changed hints is cheap. Prove it, and keep it
proven.

MEASURED stage costs on the 5.3-hour recording, which set the stakes:
  download + merge            5.5 min
  transcription                52 s
  speaker correction         33.5 min   <- must never re-run for a hint change
  break_into_paragraphs      12.8 min   <- must never re-run
  backfill_timestamps          63 s
  section headings             12 min   <- must never re-run
  frame captures              3.6 min   <- must never re-run
  concepts (10 chunks)       ~13 min    <- re-runs, correctly
  outline (10 chunks)         5.9 min   <- re-runs, correctly
  synopsis (map-reduce)        76 s     <- re-runs, correctly
So a hint iteration should cost ~20 min, against ~68 min of work it must leave alone.

WHAT TO BUILD:
  - A test that changing the hints file does not invalidate the cache key of any stage
    at or above section headings. This is the regression that would quietly destroy the
    loop, and it would only show up as "reruns feel slow", which nobody files.
  - A CLI path that reruns from hints without re-deriving upstream: the natural shape is
    to point at the existing workspace and let content addressing do the rest, so verify
    that is what actually happens rather than assuming it.

Depends on the hints file format (dt-g4qm) existing first.

## Notes

MEASURED END TO END (11:22-11:26), on a complete workspace for a short source, after the
view-count fix. Two properties, both required:

1. A RERUN OF AN UNCHANGED SOURCE IS FREE
     one-time re-baseline (view_count leaving the identity)   119 s
     rerun with nothing changed                                 4 s
     LLM calls in that rerun                                     0
     Deepgram calls in that rerun                                0
   Before the fix this same rerun bought a fresh Deepgram request and every LLM stage,
   because YouTube's view counter had moved.

2. ADDING A SEGMENT HINT ONLY INVALIDATES BELOW THE BOUNDARY
     rerun with a hint added        48 s, 3 LLM calls, 0 Deepgram
     above the boundary, untouched  transcribe, correct_speaker_turns,
                                    insert_section_headings, break_into_paragraphs
     below the boundary, re-ran     add_transcript_outline,
                                    extract_transcript_concepts, attach_transcript_index

   On the long source the untouched stages are the expensive ones: speaker correction ran
   33 min and section headings 30 min in the full pass. Keeping them out of the hint loop
   is the whole point.

Measured on the short source deliberately: it proves the same property for pennies rather
than two hours of API spend, and it is the property that matters, not the absolute times.

Caveat, stated plainly: the long-source hint rerun has still not completed end to end. It
was killed twice — once by the disk filling and once by the volume being remounted. The
boundary property is proven; the long-source wall-clock numbers for a hint rerun are not
yet measured.
