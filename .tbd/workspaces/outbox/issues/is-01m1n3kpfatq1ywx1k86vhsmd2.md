---
type: is
id: is-01m1n3kpfatq1ywx1k86vhsmd2
title: Preflight disk space before downloading media
kind: feature
status: closed
priority: 3
version: 4
spec_path: docs/project/specs/active/plan-2026-09-04-long-form-stabilization.md
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T02:22:51.369Z
updated_at: 2026-09-04T23:10:32.522Z
closed_at: 2026-09-04T23:10:32.509Z
close_reason: Free space checked on the workspace volume before download (~800 MB/h + 1 GB floor from the measured 4.0 GB for 5.26 h) and before frame capture (500 MB); stops with one line naming the volume and sizes. Tests drive run_transcription and assert on the path disk_usage was asked about.
resolution: null
duplicate_of: null
---
Estimate the download from the source duration and check free space before fetching, failing fast with a clear message the way the API-key preflight does. The failed run surfaced a raw yt-dlp UnavailableVideoError traceback ending in '[Errno 28] No space left on device' after 20 minutes of downloading.
