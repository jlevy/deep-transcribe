---
type: is
id: is-01m1n3kpt8rkxq4xa2hq48afzy
title: Report media errors without a raw traceback
kind: task
status: closed
priority: 3
version: 4
spec_path: docs/project/specs/active/plan-2026-09-04-long-form-stabilization.md
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T02:22:51.719Z
updated_at: 2026-09-04T23:10:32.931Z
closed_at: 2026-09-04T23:10:32.930Z
close_reason: ENOSPC, yt-dlp, and network (httpx.TransportError, plus EHOSTUNREACH/ENETUNREACH by errno) each map to one actionable line, exit 1, traceback to the log file only. The no-traceback test formats log records through a real Formatter, since stderr capture made the naive version pass regardless.
resolution: null
duplicate_of: null
---
Disk-full, network, and extractor failures print a full yt-dlp traceback before the friendly line. Map the common OSError and yt-dlp failures to actionable messages, consistent with the API-key preflight's tone.
