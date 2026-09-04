---
type: is
id: is-01m1q9kbn4kyzynek1b4mc3nhp
title: "PR #19 review nits (8)"
kind: task
status: open
priority: 2
version: 1
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T22:46:00.605Z
updated_at: 2026-09-04T22:46:00.605Z
---
The eight nits from the senior review of PR #19, deferred as a batch. One is likely a real bug and should go first: segment_hints.py overlaps() compares adjacent pairs only, so a hint that contains two others is not reported as overlapping.

`concept_map.py:114` — `raw_list[:MAX_CONCEPTS_PER_CHUNK]` truncates before dropping entries with
`concept_map.py:300` — `REDUCE_THRESHOLD`'s docstring says "Chunk count above which the reduce
`dt_concepts.js.jinja:149` — `layoutGraph` positions each chip at `mentions[0].t`, the order the
`dt_concepts.js.jinja:429` — the grouped outline wraps every `<li>` in its own single-item
`transcribe_commands.py:188` — `remove_processing_instructions(result)` is called on the raw
`transcript_index.py:322` — the per-unit section lookup is an O(units × headings) scan, although
`transcript_index.py:437` — with duplicated citation timestamps (94 of 1439 units in the real
`segment_hints.py:148` — `overlaps()` compares adjacent pairs only, so a hint containing two
