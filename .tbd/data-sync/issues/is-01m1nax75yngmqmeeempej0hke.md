---
type: is
id: is-01m1nax75yngmqmeeempej0hke
title: Chunk the outline and reduce the synopsis
kind: feature
status: open
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-09-04-chunked-extraction.md
labels: []
dependencies:
  - type: blocks
    target: is-01m1ng5b07vkx3hx5ghky3sxf5
parent_id: is-01m1nax66j442h166dee52zt3r
created_at: 2026-09-04T04:30:23.422Z
updated_at: 2026-09-04T06:02:21.586Z
---
Outline is already sectional, so per-chunk outlines concatenate in timeline order. Synopsis becomes map-reduce: per-chunk summaries, then a final pass over those summaries.

The reduce pass reads STRUCTURE, not text: a 5-hour transcript is 55k words but its outline is ~2k and 50-70 concepts with glosses about the same, so the reduce input is article-sized at any recording length. That headroom lets it genuinely organize rather than just concatenate — collapse near-duplicates that identity matching misses ('AI coding agents' vs 'agentic coding'), group concepts into themes once a flat list stops being a map, order the outline as a progression, and prune concepts that prove minor once the whole conversation is in view.
