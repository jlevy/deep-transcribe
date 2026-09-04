---
type: is
id: is-01m1n3kpt8rkxq4xa2hq48afzy
title: Report media errors without a raw traceback
kind: task
status: open
priority: 3
version: 3
spec_path: docs/project/specs/active/plan-2026-09-04-long-form-stabilization.md
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T02:22:51.719Z
updated_at: 2026-09-04T22:29:15.577Z
---
Disk-full, network, and extractor failures print a full yt-dlp traceback before the friendly line. Map the common OSError and yt-dlp failures to actionable messages, consistent with the API-key preflight's tone.
