---
type: is
id: is-01m1q209w2k92bfhqrfbk1njq5
title: "PR #19 review R1: segment hints never reach the analysis stages"
kind: bug
status: open
priority: 0
version: 1
labels: []
dependencies: []
parent_id: is-01m1q1zs4f81krjzenfbtmp35t
created_at: 2026-09-04T20:33:16.162Z
updated_at: 2026-09-04T20:33:16.162Z
---
BLOCKING. drop_suppressed is only reachable via split_body(hints=). No production caller passes hints: add_transcript_outline and add_transcript_description call split_body(item.body) bare; extract_transcript_concepts calls plan_chunks(scan_raw_units(body)) and never reads get_segment_hints. Hints reach only build_transcript_index, which marks for the viewer. concept_map.py:698, transcript_overview.py:292,337. Five places claim exclusion happens: CLI help, docs.md:207, README.md, HINTS_HEADER, the collapse label. Fix: thread hints into both overview actions and the concept extractor, then test the ACTIONS not drop_suppressed.
