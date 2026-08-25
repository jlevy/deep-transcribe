---
type: is
id: is-01m0vj3fjcnn506bfq8sg6v40y
title: Re-review the yt-dlp cool-off exception on each dependency refresh
kind: task
status: open
priority: 3
version: 1
labels: []
dependencies: []
created_at: 2026-08-25T04:15:53.419Z
updated_at: 2026-08-25T04:15:53.419Z
---
pyproject.toml carries a dated exclude-newer-package exception for yt-dlp (currently 2026-08-20, admitting 2026.8.19), because a 14-day cool-off leaves yt-dlp behind YouTube's extractor changes.

The trap: an exclude-newer-package entry is a CUTOFF, not a floor. Left alone it silently freezes yt-dlp at an old release — exactly what happened to the pillow entry, which pinned 2026-07-02 long after it stopped being needed and was removed in this refresh.

On every dependency refresh: bump the date to just past the newest stable yt-dlp, never to a future date, and never onto a .devN nightly. Confirm afterwards that the lock actually moved.

Policy is written up under Supply Chain Hardening in docs/development.md.
