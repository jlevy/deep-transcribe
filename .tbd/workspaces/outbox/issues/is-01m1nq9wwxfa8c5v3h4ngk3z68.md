---
type: is
id: is-01m1nq9wwxfa8c5v3h4ngk3z68
title: Keep hint reruns cheap and prove it
kind: task
status: closed
priority: 1
version: 7
spec_path: docs/project/specs/active/plan-2026-09-04-transcript-segments.md
labels: []
dependencies: []
parent_id: is-01m1n3q978x6fyhsyfm175ngy6
created_at: 2026-09-04T08:07:01.788Z
updated_at: 2026-09-05T00:27:11.731Z
closed_at: 2026-09-05T00:27:11.730Z
close_reason: "Measured at full scale (5h15m) and controlled on the short source. Same hints, rerun: 13 s. Existing hint edited: 20 min at scale (0 Deepgram, 41 LLM calls, resumed at the outline), 36 s short. First hints on a workspace that had none: repeats paragraphs and section headings once, ~45 min at scale by stage arithmetic (measured on the short source). docs.md now states both cases (0304d9b)."
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

CONTROLLED, short source (dt-freshcheck, 4 passes): p1 first run 96 s; p2 unchanged 5 s; p3 hints added for the FIRST time 62 s, re-ran break_into_paragraphs and insert_section_headings; p4 existing hint EDITED (0:20 -> 0:25) 36 s, 0 Deepgram, 3 LLM calls, formatting stages 0, resumed at add_transcript_outline. So the expensive rerun is the first application of hints to a workspace that had none; later edits resume at the outline, which is the loop a user actually iterates in. At-scale hint-edit run in flight to supply the minutes.
