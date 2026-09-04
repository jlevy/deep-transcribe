---
type: is
id: is-01m1n3q978x6fyhsyfm175ngy6
title: Transcript segments with default suppression
kind: feature
status: open
priority: 1
version: 13
spec_path: docs/project/specs/active/plan-2026-09-04-transcript-segments.md
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
child_order_hints:
  - is-01m1n3w2gnfy82syecqepy5b93
  - is-01m1n3w35gh277jkr5rreywjsd
  - is-01m1n3w3s56t6zzyf0e8zbzcaq
  - is-01m1n3w54cw73gbx7zft0av37v
  - is-01m1n9pf2qwyfejb1xdjzx385k
  - is-01m1n9rj7r4bw9maq6wcggj6kz
  - is-01m1na58vampj3d053x9qddjf3
  - is-01m1nq9wwxfa8c5v3h4ngk3z68
created_at: 2026-09-04T02:24:48.871Z
updated_at: 2026-09-04T08:07:01.788Z
---
MEASURED against Lex #501 (5.3h) before designing:
- 23 YouTube chapters with exact boundaries and human titles, including 'Episode highlight' (0:00-1:27) and 'Introduction' (1:27-2:56). Excellent free skeleton.
- NO chapter marks a sponsor; no chapter title contains any sponsor name.
- The description names 8 sponsors, but 5 never appear in the transcript, and the 3 that do are organic conversation (Shopify layoffs and its CTO, Perplexity and Plaud as products discussed).
- Searching the whole transcript for ad-read phrasing ('brought to you by', 'this episode is sponsored', 'use code') returns ZERO matches.
=> This episode has no in-audio sponsor reads despite naming 8 sponsors. Description metadata is not evidence an ad exists; name matching yields only false positives and would have suppressed real conversation.

DESIGN: segments partition the whole timeline; each states a purpose (content/preview/intro/sponsor/outro) and whether it is suppressed by default, with source recorded as chapter or detected. Chapters seed the partition where they exist; detection fills gaps and handles sources without chapters. Suppressed passages collapse in place, never delete. See plan-2026-09-04-transcript-segments.md.

## Notes

DESIGN REFRAMED by the user (2026-09-04), and it is simpler than what the spec drafted.

Segment handling does NOT have to be fully automated. What matters is the loop:

  run the tool -> look at the output -> revise the hints -> rerun

and the rerun must be cheap: it must not redo the parts that are already correct,
above all the transcript. An agent can drive this loop itself — run, inspect, fix the
hints, rerun — as long as rerunning is not a fresh five-hour pipeline.

WHAT THIS IMPLIES ARCHITECTURALLY, and it is the load-bearing constraint:

Hints must be an input to a LATE stage. Content-addressed caching already gives cheap
reruns for free, but only for stages upstream of the changed input. So the cut is:

  NEVER re-run when hints change   download, transcription, speaker correction (33.5 min
                                   at 5.3 h), break_into_paragraphs (12.8 min),
                                   backfill_timestamps, section headings, frame captures
  RE-RUN when hints change         concepts (~13 min), outline (~6 min), synopsis (~1 min),
                                   index, export

That is roughly 20 minutes per iteration against 60+ for the untouched stages, and the
expensive half is exactly the half that hints have no business changing. If a hint ever
feeds a stage above that line, the loop stops being usable.

So a hint marks a time range and a purpose, and the effect is: excluded from analysis,
and grayed/collapsed rather than deleted in the views. Detection can propose hints; the
file is the contract and a human or agent can write it by hand.

Automatic detection becomes a convenience that writes a first draft of the hints file,
not a prerequisite. dt-88st (detect_segments) drops in priority accordingly; dt-g4qm
(the file format and IO) rises, because the format IS the interface.
