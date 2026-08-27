---
type: is
id: is-01m12k2db1dqxc18fmmsjcy70x
title: Raise the kash-media floor and release deep-transcribe v0.1.14
kind: task
status: open
priority: 1
version: 1
labels: []
dependencies: []
parent_id: is-01m1118hwdhra16fmaz6jd1smt
created_at: 2026-08-27T21:47:27.968Z
updated_at: 2026-08-27T21:47:27.968Z
---
After kash-media 0.4.8 publishes:

1. uv add --exclude-newer "14 days" "kash-media>=0.4.8,<0.5"
2. uv lock, make lint && make test
3. Tag v0.1.14

jlevy/deep-transcribe#16 can merge before this — it reads every field through .get() with isinstance guards, so it degrades safely on the current releases. This bump is what guarantees the discovery fields are actually present.

Optional cleanup: deep-transcribe imports kash.exec and kash.model directly but declares no kash-shell dependency, the same gap that was just fixed in kash-media.

Current: deep-transcribe v0.1.13.
