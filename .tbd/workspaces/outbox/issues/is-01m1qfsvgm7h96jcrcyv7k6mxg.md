---
type: is
id: is-01m1qfsvgm7h96jcrcyv7k6mxg
title: Cap section-heading density; use publisher chapters as the skeleton
kind: feature
status: open
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-09-04-agent-iteration-loop.md
labels: []
dependencies: []
parent_id: is-01m1qfkw8vxpzmyds5qsxm798b
child_order_hints:
  - is-01m1n9pf2qwyfejb1xdjzx385k
created_at: 2026-09-05T00:34:24.914Z
updated_at: 2026-09-05T00:41:23.341Z
---
Measured on Lex #501: insert_section_headings (kash, WINDOW_128_PARA) produced 206 headings over 5h15m — one every 1.5 minutes — and the outline is sectional, so it inherits all 206 entries. A reader of a five-hour interview wants roughly 30–60 sections. No flag controls density and processing instructions do not reach this stage.

Two parts. (1) dt-pq0j: when the source carries publisher chapters (YouTube: 23 human-written chapters with exact boundaries on this episode), insert them as the H2 skeleton by timestamp and demote model headings to H3 inside them. (2) A density target for model headings, like the frame cap: --headings-every MINUTES or a per-hour target, applied as a consolidation pass that reads only the headings and each section's opening line (cheap) and merges to the target. Default around one per 5–8 minutes. Outline, timeline rows and index must handle H2/H3. Verify on the full export: expect ~40–60 top-level entries.

## Notes

DESIGN, verified against the code on 2026-09-04. transcript_index._H2_PATTERN is ^##(?!#): the index, sections, outline chunking (split_body cuts on '## ') and timeline see only H2 and ignore H3. So: (1) at _prepare_source_item, fetch chapters with a metadata-only yt_dlp call (this video: 23 chapters, ~3 s) and store them on the resource as extra.chapters [{start_time, title}] — stable, unlike view_count; (2) a new deterministic stage insert_chapter_headings, placed before insert_section_headings, inserts '## <title>' before the first unit whose citation >= start_time; (3) after kash's insert_section_headings (which emits '## '), a deterministic demote step turns every '## ' whose text is not a chapter title into '### '. No consolidation pass is needed for chaptered sources: the outline becomes 23 sectional entries with their key points, the timeline 23 blocks, and the 206 model headings remain as H3 sub-headings in the transcript. For sources without chapters, keep today's behaviour and leave the density cap as a follow-on. Cost: the resource gains a key once (one re-baseline), and the new stage sits above section headings, so the first run pays speaker-correction-onward (~75 min); later runs are unaffected. Tests: chapter insertion by timestamp incl. a chapter that starts mid-paragraph (insert before the next unit), demotion leaves chapter H2s alone, a source with no chapters is byte-identical to today, and the index reports exactly 23 sections on a body built from the real chapter list.
