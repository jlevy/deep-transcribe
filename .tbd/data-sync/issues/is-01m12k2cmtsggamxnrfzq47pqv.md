---
type: is
id: is-01m12k2cmtsggamxnrfzq47pqv
title: Release kash-shell v0.4.10 with media discovery metadata
kind: task
status: open
priority: 1
version: 2
labels: []
dependencies:
  - type: blocks
    target: is-01m12k2d0v1agkrwgs21dtnxs9
parent_id: is-01m1118hwdhra16fmaz6jd1smt
created_at: 2026-08-27T21:47:27.242Z
updated_at: 2026-08-27T21:47:27.642Z
---
Merge jlevy/kash#21 (green) and tag v0.4.10.

It adds channel, uploader, categories, and tags to MediaMetadata and copies them into Item.extra. Nothing downstream can move until this is on PyPI: kash-media's extractor passes these as keyword arguments to a plain dataclass, so any older kash-shell raises TypeError.

Current: kash-shell v0.4.9.
