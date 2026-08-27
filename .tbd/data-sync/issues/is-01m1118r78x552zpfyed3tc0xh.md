---
type: is
id: is-01m1118r78x552zpfyed3tc0xh
title: Audit yt-dlp extraction and source-context ownership
kind: task
status: closed
priority: 1
version: 6
labels: []
dependencies:
  - type: blocks
    target: is-01m1118x39wbaje1bdf6nxd782
  - type: blocks
    target: is-01m1118xbm3dbmh234fpr1bjea
  - type: blocks
    target: is-01m111ba1wrc83cj7cf21vpcdt
parent_id: is-01m1118hwdhra16fmaz6jd1smt
created_at: 2026-08-27T07:17:06.919Z
updated_at: 2026-08-27T07:18:31.081Z
closed_at: 2026-08-27T07:18:31.080Z
close_reason: Confirmed that Deep Transcribe prepares URLs before Kash Media registers its services, so fresh YouTube sources use generic HTML metadata instead of yt-dlp. Registering the media kit in Deep Transcribe is the local base fix; retaining channel names, categories, and tags is a reusable upstream Kash metadata concern.
resolution: null
duplicate_of: null
---
Reproduce fresh URL preparation, enumerate useful yt-dlp fields, trace prompt propagation and cache behavior, and decide whether changes belong in Deep Transcribe or reusable Kash primitives.
