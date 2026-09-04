---
type: is
id: is-01m1nax6vqj3dqbc25qp7hk7nf
title: Extract concepts per chunk and merge
kind: feature
status: closed
priority: 0
version: 3
spec_path: docs/project/specs/active/plan-2026-09-04-chunked-extraction.md
labels: []
dependencies: []
parent_id: is-01m1nax66j442h166dee52zt3r
created_at: 2026-09-04T04:30:23.093Z
updated_at: 2026-09-04T06:59:26.507Z
closed_at: 2026-09-04T06:59:26.506Z
close_reason: Implemented in d73a88d. 24 -> 119 concepts on the 5.3-hour run (4.6 -> 22.6 per hour), span median 6.9 -> 2.3 min, zero spans over 15% of the recording, 97 relations resolved after the merge. Partial chunk failure is tolerated.
resolution: null
duplicate_of: null
---
Make MAX_CONCEPTS per-chunk (8-12) instead of per-recording, so a 5h episode yields ~50-70 concepts and 12h ~120-170 while a short talk is unchanged. Merge by normalized id then label: union mentions and speakers, span from earliest to latest, first non-empty gloss. Resolve relations ONCE over the merged set so a relation naming a concept from another chunk survives.

## Notes

MEASURED on Lex #501 (5.26 h), whole-document vs 10 chunks of 30 min:

                       before    after
  concepts              24       119
  per hour               4.6      22.6
  span median (min)      6.9       2.3
  spans >15% of run      6         0
  relations kept        (n/a)     97
  wall clock            ~70 s     429 s (10 sequential calls, ~43 s each)

Chunk plan on the real transcript, target 30 min: 10 chunks of 5,297-6,385 words, each
cut at a section boundary. Target 60 min gives 6 chunks but a ragged 2,274-word tail, so
30 min is the better default.

Kind mix came out 95 claims / 13 entities / 11 topics — heavily claim-weighted. Worth
watching, but the claims read as real claims, so not obviously wrong.

Two things the run exposed, both fixed in d73a88d:
  - One chunk in ten returned an unterminated ```json fence and aborted the whole stage.
    Ten calls means ten chances of that, so a failed chunk is now skipped rather than
    fatal.
  - Labels drifted from sentence case in early chunks to title case in later ones. The
    prompt now asks for sentence case.

Left for the reduce pass (dt-ndlx): near-duplicates across chunk seams that identity
matching cannot catch, e.g. "AI psychosis" vs "AI psychosis / delirium framing";
"Glimmers of AGI" vs "Glimmers of AI consciousness"; three separate Omarchy entities
("Omarchy / Omarchy Quattro", "Omakub Linux distribution", "Omarchi (Umachi) Linux
Distro"); "Omakub/Quattro written 100% by AI" vs "Quattro built primarily by AI agents".
