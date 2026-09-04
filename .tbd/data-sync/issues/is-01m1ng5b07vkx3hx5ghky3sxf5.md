---
type: is
id: is-01m1ng5b07vkx3hx5ghky3sxf5
title: Make the outline legible at hundreds of sections
kind: task
status: in_progress
priority: 1
version: 3
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T06:02:12.358Z
updated_at: 2026-09-04T08:29:57.889Z
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

## Notes

IMPLEMENTED in 56def37, not yet seen rendered.

The outline is grouped under the concept reduce pass's themes, by time span, reusing the
same collapsible container as the themed concept list. Expected effect on the 5.3-hour
run: 172 top-level entries collapse to 12 theme lines.

NOT YET VERIFIED IN A BROWSER. The docs available when this was written had either the
new chunked outline or the themed concepts, never both — the clean full re-run started
at 01:18 is the first document that will have both. Check on that export:
  - 12 theme groups appear in the outline, collapsed
  - each group's count matches the sections it holds
  - the timeline time chips still work inside the groups (they are moved, not rebuilt)
  - print shows every group expanded
