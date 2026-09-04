---
type: is
id: is-01m1n6gctkkxnqy75w1z619mfs
title: "Track upstream kash PR #23 through release"
kind: task
status: open
priority: 1
version: 2
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T03:13:28.914Z
updated_at: 2026-09-04T03:31:55.966Z
---
Two upstream PRs, both CI-green, consumed locally via editable overlays:
  kash PR #23 — TranscriptionLimits (long-audio request budget)
  kash-media PR #12 — VideoDownloadOptions, remux instead of re-encode

Release sequence once the long-form run validates end to end:
  1. merge kash #23, cut a kash release
  2. merge kash-media #12, bump its kash-shell pin, cut a kash-media release
  3. bump deep-transcribe's kash-shell and kash-media pins
  4. drop the local editable overlays (uv pip install -e ../kash, ../kash-media --no-deps)

Note: both local checkouts were moved from v0.3.37/v0.3.19 to current main to do this work, so their git state differs from how they were found.
