---
type: is
id: is-01kxj8kybb14nmge2eq43qt0pq
title: Fix local MP4 frame-capture path resolution
kind: bug
status: closed
priority: 1
version: 1
labels: []
dependencies: []
parent_id: null
due_date: null
deferred_until: null
created_at: 2026-07-15T04:41:56.000Z
updated_at: 2026-07-15T04:55:40.000Z
closed_at: 2026-07-15T04:55:40.000Z
close_reason: Fixed kash workspace resource resolution in v0.4.5 with a focused regression test. A fresh real local MP4 completed the full annotated Deep Transcribe pipeline from an unrelated cwd; 19/19 rendered frame images loaded, expected metadata and speaker names were present, and the export had no overflow or path errors.
extensions:
  beads:
    original_id: dt-zeg.8
    imported_at: 2026-07-15T06:49:51.726Z
---
A local MP4 imported into the workspace transcribes successfully but insert_frame_captures passes the workspace-relative original filename to cache_resource, which resolves it against the process working directory and raises FileNotFound.

## Notes

Reported from the globally installed Deep Transcribe while running in ~/tmp. Trace ends at insert_frame_captures -> cache_resource with a bare resource filename.
Root cause confirmed in kash cache_resource: imported resources have both store_path and a basename-only original_filename, but the helper ignored store_path and resolved original_filename against cwd. Fix is a generic workspace-resource resolution path plus regression test.
