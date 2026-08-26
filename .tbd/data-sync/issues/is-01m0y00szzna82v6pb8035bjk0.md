---
type: is
id: is-01m0y00szzna82v6pb8035bjk0
title: Fix local MP4 workspace disk amplification
kind: bug
status: closed
priority: 1
version: 6
labels: []
dependencies: []
parent_id: is-01m0xwzrh7debayb7dhcrz1d9y
created_at: 2026-08-26T02:57:34.717Z
updated_at: 2026-08-26T03:46:08.970Z
closed_at: 2026-08-26T03:46:08.969Z
close_reason: Implemented, regression-tested, and validated with real private and public end-to-end workflows.
resolution: null
duplicate_of: null
---
Prevent local media from being copied into the workspace before kash media caching; cover the locator behavior and validate a large local MP4 end to end.

## Notes

Validated with a large real local MP4: the source is registered as a file URL, the raw transcript and annotated frame-capture pipeline complete, and no source MP4 is copied into the workspace. Unit and release-runbook coverage added.
