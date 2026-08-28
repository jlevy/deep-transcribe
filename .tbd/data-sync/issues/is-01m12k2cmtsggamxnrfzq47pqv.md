---
type: is
id: is-01m12k2cmtsggamxnrfzq47pqv
title: Release kash-shell v0.4.10 with media discovery metadata
kind: task
status: closed
priority: 1
version: 3
labels: []
dependencies:
  - type: blocks
    target: is-01m12k2d0v1agkrwgs21dtnxs9
parent_id: is-01m1118hwdhra16fmaz6jd1smt
created_at: 2026-08-27T21:47:27.242Z
updated_at: 2026-08-28T04:20:11.464Z
closed_at: 2026-08-28T04:20:11.463Z
close_reason: "Released kash-shell v0.4.10 (GitHub release -> PyPI, confirmed live). Carries both PR #21's discovery metadata fields and PR #22's fix for web search on Anthropic models."
resolution: null
duplicate_of: null
---
Merge jlevy/kash#21 (green) and tag v0.4.10.

It adds channel, uploader, categories, and tags to MediaMetadata and copies them into Item.extra. Nothing downstream can move until this is on PyPI: kash-media's extractor passes these as keyword arguments to a plain dataclass, so any older kash-shell raises TypeError.

Current: kash-shell v0.4.9.
