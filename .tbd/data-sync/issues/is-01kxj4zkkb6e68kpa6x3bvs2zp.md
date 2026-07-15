---
type: is
id: is-01kxj4zkkb6e68kpa6x3bvs2zp
title: Canonicalize equivalent YouTube URLs across media cache consumers
kind: bug
status: closed
priority: 1
version: 5
labels: []
dependencies:
  - type: blocks
    target: is-01kxj4zkw8vp8g4ebs496hwdgw
parent_id: is-01kxj4xxyfwmxmk3z9mebcf92x
created_at: 2026-07-15T05:46:19.624Z
updated_at: 2026-07-15T06:48:58.354Z
closed_at: 2026-07-15T06:48:58.354Z
close_reason: Implemented, validated end to end, merged, and released in the patch dependency chain ending with Deep Transcribe 0.1.9.
---
Canonicalize recognized media URLs before media cache key generation so youtu.be share links, watch URLs, and tracking parameters reuse the same transcription/video assets across transcription and frame-capture stages.

## Notes

Implemented canonicalization inside MediaCache.cache before cache-key generation. Regression proves youtu.be tracking URL reuses canonical watch-URL video without downloader call. kash-shell lint/type and 311 tests pass; annotated SNL frame capture reused canonical audio/video.
