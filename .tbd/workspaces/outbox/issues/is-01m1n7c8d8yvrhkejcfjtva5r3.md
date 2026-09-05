---
type: is
id: is-01m1n7c8d8yvrhkejcfjtva5r3
title: Video download re-encoded instead of remuxing
kind: bug
status: closed
priority: 0
version: 2
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T03:28:41.895Z
updated_at: 2026-09-04T03:28:42.414Z
closed_at: 2026-09-04T03:28:42.413Z
close_reason: "Fixed in kash-media PR #12; verified by format-selection comparison on the real source (webm merge -> mp4 merge, same video stream)"
resolution: null
duplicate_of: null
---
FIXED in kash-media PR #12. bestvideo picked an mp4 stream while bestaudio picked webm/opus, so the merge produced a webm container and FFmpegVideoConvertor then re-encoded the whole video to mp4 — hours of CPU on a 5.3-hour source, before transcription could start. Fixed by preferring m4a audio (merge yields mp4 directly), using FFmpegVideoRemuxer instead of the convertor, and capping height at 1080 by default. VideoDownloadOptions exposes max_height, prefer_compatible, and a format override.
