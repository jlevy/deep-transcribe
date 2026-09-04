---
type: is
id: is-01m1n3kp47xvjpgapq51syjb7b
title: Transcription downloads video before knowing it is needed
kind: bug
status: open
priority: 3
version: 3
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T02:22:51.014Z
updated_at: 2026-09-04T02:44:37.047Z
---
CORRECTED SCOPE: video IS needed for frame captures, so on --annotated/--deep (the default) the download is not wasted, just taken earlier than necessary.

The real defect is that it is unconditional. MediaCache.transcribe calls self.cache(url, refetch) with default media_types ('Cache all formats since we usually will want them'), so a --basic or --formatted run — which never captures frames — still pulls gigabytes of video it will never open. On a 5.3-hour podcast that is the difference between roughly 450 MB of audio and multiple GB.

Fix: transcription requests audio only; the frame-capture stage caches video itself when it actually runs (it already calls cache_resource). Video then downloads exactly when a run needs it.

Possible follow-on: frame captures may not need the highest-quality stream. Requesting a lower-resolution video for frame extraction would cut the download further for the presets that do need it.
