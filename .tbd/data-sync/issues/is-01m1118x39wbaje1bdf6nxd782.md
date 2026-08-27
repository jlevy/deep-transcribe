---
type: is
id: is-01m1118x39wbaje1bdf6nxd782
title: Fetch and persist optional media metadata before transcription
kind: feature
status: closed
priority: 1
version: 6
labels: []
dependencies:
  - type: blocks
    target: is-01m111937sae4xnggpx66hd9v4
  - type: blocks
    target: is-01m11193gad6ckk9q3dbgzyrh1
  - type: blocks
    target: is-01m111bhjv1epzw4m0tbs9b84p
parent_id: is-01m1118hwdhra16fmaz6jd1smt
created_at: 2026-08-27T07:17:11.912Z
updated_at: 2026-08-27T07:42:15.432Z
closed_at: 2026-08-27T07:42:15.425Z
close_reason: Deep Transcribe now prepares supported URLs through registered media extractors and enriches incomplete legacy cache entries without invalidating raw transcription.
resolution: null
duplicate_of: null
---
Register the media extractor before URL preparation, retain useful bounded source fields, keep the path best effort where metadata is unavailable, and cover fresh and cached URL resources with deterministic tests.
