---
type: is
id: is-01m1n6gctkkxnqy75w1z619mfs
title: "Track upstream kash PR #23 through release"
kind: task
status: open
priority: 1
version: 1
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T03:13:28.914Z
updated_at: 2026-09-04T03:13:28.914Z
---
kash PR #23 exposes TranscriptionLimits (long-audio timeout policy). Deep-transcribe currently consumes it via an editable overlay of the local kash checkout. Sequence once validated end to end: merge PR #23, cut a kash release, then bump deep-transcribe's kash-shell pin and drop the local overlay. Note the local kash and kash-media checkouts were moved from v0.3.37/v0.3.19 to current main to do this work.
