---
type: is
id: is-01m1qfsvgm7h96jcrcyv7k6mxg
title: Cap section-heading density; use publisher chapters as the skeleton
kind: feature
status: open
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-09-04-agent-iteration-loop.md
labels: []
dependencies: []
parent_id: is-01m1qfkw8vxpzmyds5qsxm798b
child_order_hints:
  - is-01m1n9pf2qwyfejb1xdjzx385k
created_at: 2026-09-05T00:34:24.914Z
updated_at: 2026-09-05T00:38:11.316Z
---
Measured on Lex #501: insert_section_headings (kash, WINDOW_128_PARA) produced 206 headings over 5h15m — one every 1.5 minutes — and the outline is sectional, so it inherits all 206 entries. A reader of a five-hour interview wants roughly 30–60 sections. No flag controls density and processing instructions do not reach this stage.

Two parts. (1) dt-pq0j: when the source carries publisher chapters (YouTube: 23 human-written chapters with exact boundaries on this episode), insert them as the H2 skeleton by timestamp and demote model headings to H3 inside them. (2) A density target for model headings, like the frame cap: --headings-every MINUTES or a per-hour target, applied as a consolidation pass that reads only the headings and each section's opening line (cheap) and merges to the target. Default around one per 5–8 minutes. Outline, timeline rows and index must handle H2/H3. Verify on the full export: expect ~40–60 top-level entries.

## Notes

The stored resource carries NO chapters: kash's YouTube metadata keeps categories/channel/duration/tags/uploader but not yt-dlp's chapters list. Part (1) needs the chapters fetched (yt-dlp info has them; add to the kash media kit or fetch directly) before they can seed the H2 skeleton.
