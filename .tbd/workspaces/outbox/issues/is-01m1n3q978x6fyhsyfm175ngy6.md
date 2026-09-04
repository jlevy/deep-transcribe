---
type: is
id: is-01m1n3q978x6fyhsyfm175ngy6
title: Transcript segments with default suppression
kind: feature
status: open
priority: 1
version: 14
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
updated_at: 2026-09-04T09:07:59.066Z
---
MEASURED against Lex #501 (5.3h) before designing:
- 23 YouTube chapters with exact boundaries and human titles, including 'Episode highlight' (0:00-1:27) and 'Introduction' (1:27-2:56). Excellent free skeleton.
- NO chapter marks a sponsor; no chapter title contains any sponsor name.
- The description names 8 sponsors, but 5 never appear in the transcript, and the 3 that do are organic conversation (Shopify layoffs and its CTO, Perplexity and Plaud as products discussed).
- Searching the whole transcript for ad-read phrasing ('brought to you by', 'this episode is sponsored', 'use code') returns ZERO matches.
=> This episode has no in-audio sponsor reads despite naming 8 sponsors. Description metadata is not evidence an ad exists; name matching yields only false positives and would have suppressed real conversation.

DESIGN: segments partition the whole timeline; each states a purpose (content/preview/intro/sponsor/outro) and whether it is suppressed by default, with source recorded as chapter or detected. Chapters seed the partition where they exist; detection fills gaps and handles sources without chapters. Suppressed passages collapse in place, never delete. See plan-2026-09-04-transcript-segments.md.

## Notes

SEGMENTS FOUNDATION LANDED, following the user's reframing: the loop matters, full
automation does not.

  dt-g4qm  hints file format, parser, writer, validation      1c1f02f
           CLI `--segments PATH`                              1f56b83
  dt-n3gh  suppressed units excluded from chunking, and       070cd61
           suppressed sections excluded from split_body
  dt-hesk  index marks units, transcript collapses runs       5172ce1

The cache cut, which is the load-bearing part: hints ride to the same late boundary as
the processing instructions (_attach_late_inputs). Everything above it — transcription,
speaker correction, paragraphs, section headings — keeps its identity when a hint
changes; everything below is redone. Hints are carried to that boundary as YAML TEXT
rather than a mapping, so the action's identity is a plain string and two files that
differ only in key order hash the same.

STILL TO VERIFY (dt-kap1), and it is the claim the whole design rests on: that editing a
hint and rerunning actually reuses the expensive stages. A hints file for the Lex #501
teaser is ready at /Volumes/spud-ext1/tmp/dt-scratch/segments-lex501.yml marking
0:00:00-0:02:12, which is three unrelated topics — AI progress, risk and the Overton
window, the peak human experience — before the interview starts at "From Manual
Programming to Agentic Engineering". Rerun the same command with `--segments` against
the finished dt-final workspace and check which stages re-run. Expect: transcription,
speaker correction, paragraphs and sections all cached; frames re-run (they sit below
the boundary, ~4 min, wasteful but tolerable); outline, synopsis, concepts, index and
export re-run, which is the point.

If frame captures turn out to dominate the rerun cost, the fix is to move
insert_frame_captures above the boundary — but note that puts img tags into the outline
prompt's input, which is why it is not already there.
