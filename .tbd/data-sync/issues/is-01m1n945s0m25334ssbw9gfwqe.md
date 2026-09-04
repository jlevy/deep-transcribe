---
type: is
id: is-01m1n945s0m25334ssbw9gfwqe
title: Support audio up to 12 hours end to end
kind: feature
status: open
priority: 0
version: 3
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T03:59:14.207Z
updated_at: 2026-09-04T07:50:28.292Z
---
Target: 12 hours of audio works end to end.

CLEARED so far, with measurements:
- Deepgram size cap 2 GB: 5.26h yields a 57 MB 16k mp3, so 12h is ~130 MB. Fine.
- Deepgram processing cap 600s (504 otherwise): 5.26h took ~52s, about 364x realtime, so 12h is ~120s. Fine.
- Client request budget: scales with duration (kash #23); 12h asks for 11,300s, capped at the 7,200s ceiling, far above the ~120s actually needed.
- Memory: WAS a hard blocker. pydub decoded whole files to PCM (~3.3 GB for 5.26h, ~7.6 GB at 12h). Now streams through ffmpeg at ~106 MB peak, flat in duration (kash f298841).

STILL TO VERIFY at 12h:
- LLM stages that read the whole transcript (sections, outline, synopsis, concepts). A 12h transcript is roughly 110k words / 150k tokens and may exceed context; speaker correction already chunks. This is the main open risk and overlaps dt-sfoz.
- Frame captures at paragraph granularity: hundreds to thousands of ffmpeg seeks and a large assets directory.
- Output legibility and HTML/PDF size at that length.

## Notes

MEASURED at 5.26h: 55,122 words in the transcript = ~74k tokens, about 10,480 words/hour.

Projection for whole-transcript stages (outline, synopsis, concepts all send the entire document in one call):
  5.26h ~74k tokens   fits comfortably
  8h    ~113k         fits
  12h   ~170k         fits a 200k context, but tight once prompt and output are added
  14h   ~198k         at the limit
  16h+                exceeds

So 12 hours works on a 200k-context model, with little headroom. Beyond ~13-14h these stages need the same windowed map-reduce treatment the sectioning pass already uses. Speaker correction already windows and took 33.5 min for 5.26h (~40 LLM calls), scaling linearly.
UPDATE after chunked extraction (d73a88d) and chunked outline/synopsis (6a01bd8):

THE CONTEXT CEILING IS GONE, not merely raised. The projection above — 12h fits a 200k
context with little headroom, 14h at the limit, 16h+ over — described stages that sent
the whole document. None of them do now:
  outline     one call per ~30 min chunk, concatenated
  synopsis    one summary per chunk, then one reduce over the summaries
  concepts    one call per chunk, then one reduce over the merged map
The reduce inputs are the size of the analysis, not of the transcript, so they are
article-sized whatever the recording's length. See dt-2sam for the full call-site audit.

What grows now is the NUMBER of calls, linearly with duration. At 30-minute chunks a
twelve-hour recording is 24 outline calls, 24 chunk summaries, 24 concept calls, plus
two reduces. From the measured 5.26h run (~43 s per concept chunk, ~780 s for 10 chunks
plus a reduce), twelve hours of concept extraction is roughly 20 minutes wall clock and
the outline about the same, both trivially parallelizable later if that matters.

Speaker correction remains the long pole: 33.5 min at 5.26 h, windowed and linear, so
roughly 75 min at twelve hours.

REMAINING at 12h, unchanged: frame captures (density cap, dt-wgaf) and output legibility
(the timeline now wraps into 12 one-hour rows at that length, dt-1gl6). Nothing has
actually run at twelve hours; the arithmetic and the audit both say it completes.
