---
type: is
id: is-01m1ng5b07vkx3hx5ghky3sxf5
title: Make the outline legible at hundreds of sections
kind: task
status: closed
priority: 1
version: 5
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T06:02:12.358Z
updated_at: 2026-09-04T16:11:19.073Z
closed_at: 2026-09-04T16:11:19.072Z
close_reason: "Verified in a browser: 199 outline entries in 24 theme groups, largest 23, none under 3, each headed with the time its stretch begins. Two assignment bugs found and fixed in the process."
resolution: null
duplicate_of: null
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

RENDERING VERIFIED IN A BROWSER (04:25), on an export built from the batched reduce's
themed map:

                          before      after
  Concepts panel        18,623 px    865 px
  definition list       14,901 px    791 px
  concept theme groups          0    13, all collapsed
  per-theme graphs              0    13 (114 chips, none stuck at x=0)
  global graph                  1    0, correctly suppressed
  outline groups                5    24, largest 23, none under 3
  whole document       235,380 px    180,232 px
  timeline rows                11    11
  frames / broken          168 / 0   168 / 0

The Concepts panel is the headline: 18,623 px to 865 px, about 21x.

TWO BUGS FOUND AND FIXED IN THIS PASS, both only visible with real themed data:
  The outline's theme assignment used "which theme's span covers this time", and themes
  overlap because a conversation returns to its subjects. First-match-wins gave one
  heading 162 of 199 entries. Nearest-concept-in-time fixed it.
  With proximity assignment a theme heads several stretches, which read as duplicated
  headings. The heads now carry the time their stretch begins.

The graph-span fix made earlier without being able to see it held: chipsAtZero is 0.
