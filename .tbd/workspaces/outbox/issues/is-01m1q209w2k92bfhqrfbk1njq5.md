---
type: is
id: is-01m1q209w2k92bfhqrfbk1njq5
title: "PR #19 review R1: segment hints never reach the analysis stages"
kind: bug
status: closed
priority: 0
version: 3
labels: []
dependencies: []
parent_id: is-01m1q1zs4f81krjzenfbtmp35t
created_at: 2026-09-04T20:33:16.162Z
updated_at: 2026-09-04T20:37:57.964Z
closed_at: 2026-09-04T20:37:57.963Z
close_reason: Hints now reach both overview actions and the concept extractor; tests drive the actions and were verified to fail without the fix.
resolution: null
duplicate_of: null
---
BLOCKING. drop_suppressed is only reachable via split_body(hints=). No production caller passes hints: add_transcript_outline and add_transcript_description call split_body(item.body) bare; extract_transcript_concepts calls plan_chunks(scan_raw_units(body)) and never reads get_segment_hints. Hints reach only build_transcript_index, which marks for the viewer. concept_map.py:698, transcript_overview.py:292,337. Five places claim exclusion happens: CLI help, docs.md:207, README.md, HINTS_HEADER, the collapse label. Fix: thread hints into both overview actions and the concept extractor, then test the ACTIONS not drop_suppressed.
