---
type: is
id: is-01m1nax75yngmqmeeempej0hke
title: Chunk the outline and reduce the synopsis
kind: feature
status: open
priority: 0
version: 4
spec_path: docs/project/specs/active/plan-2026-09-04-chunked-extraction.md
labels: []
dependencies:
  - type: blocks
    target: is-01m1ng5b07vkx3hx5ghky3sxf5
parent_id: is-01m1nax66j442h166dee52zt3r
created_at: 2026-09-04T04:30:23.422Z
updated_at: 2026-09-04T07:00:23.233Z
---
Outline is already sectional, so per-chunk outlines concatenate in timeline order. Synopsis becomes map-reduce: per-chunk summaries, then a final pass over those summaries.

The reduce pass reads STRUCTURE, not text: a 5-hour transcript is 55k words but its outline is ~2k and 50-70 concepts with glosses about the same, so the reduce input is article-sized at any recording length. That headroom lets it genuinely organize rather than just concatenate — collapse near-duplicates that identity matching misses ('AI coding agents' vs 'agentic coding'), group concepts into themes once a flat list stops being a map, order the outline as a progression, and prune concepts that prove minor once the whole conversation is in view.

## Notes

MEASURED after chunked extraction landed (d73a88d), on the 5.3-hour export at 1200 px:

  concepts                119
  Concepts panel height   18,399 px — about 20 screens
  concept entries         214 (each concept renders in the map and again under Claims)
  chips                   452
  per-concept tracks      119
  graph elements          455
  whole document          203,270 px

So the spec's open question is answered: a flat list of 119 does not stay legible. This
is now the binding constraint on the output, not the concept count — chunking gave the
analysis the coverage it needed and handed the legibility problem to this pass.

Near-duplicates the identity merge cannot see, from the same run, as concrete targets:
  "AI psychosis" / "AI psychosis / delirium framing"
  "Glimmers of AGI" / "Glimmers of AI consciousness"
  "Omarchy / Omarchy Quattro Linux distribution" / "Omakub Linux distribution" /
      "Omarchi (Umachi) Linux Distro"
  "Omakub/Quattro written 100% by AI" / "Quattro built primarily by AI agents"
  "Engagement-maximizing algorithms harm society" / "Engagement-driven algorithm reward
      function"

Kind mix is skewed: 95 claims, 13 entities, 11 topics. Pruning in the reduce pass should
take that into account rather than trimming uniformly.
