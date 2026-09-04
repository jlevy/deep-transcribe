---
type: is
id: is-01m1ng5b07vkx3hx5ghky3sxf5
title: Make the outline legible at hundreds of sections
kind: task
status: open
priority: 1
version: 1
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T06:02:12.358Z
updated_at: 2026-09-04T06:02:12.358Z
---
The Outline view renders one line per section. That is right for 20 sections and unusable
for 194.

MEASURED on Lex #501 (5.26 h):
  194 sections from insert_section_headings = one per 1.6 min, against 23 publisher
  chapters for the same recording. Section words: median 260, p10 128, p90 580,
  min 44, max 953. 60 sections are under 200 words; 13 under 100.

The sections themselves are reasonable transcript divisions — the failure is presenting
194 flat peers as a navigational overview. Two candidate directions, not exclusive:
  1. Group sections into a coarser tier for the outline. dt-ndlx's reduce pass already
     produces a smaller organized structure over the chunk outputs; that structure is the
     natural top level, with sections nested under it.
  2. Use publisher chapters as the top tier where they exist (dt-pq0j) — 23 chapters over
     194 sections is exactly the ratio a two-level outline wants.

Whatever the grouping, the Outline should open collapsed to the top tier and the timeline
cross-references should still resolve to individual sections. Depends on dt-ndlx and
dt-pq0j landing first, since both supply the coarse tier.
