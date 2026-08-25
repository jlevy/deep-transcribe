---
type: is
id: is-01m0vj37a16qkkh9y6at2wy4cc
title: "Upstream: widen chopdiff's flexdoc cap so flexdoc 0.4.x can resolve"
kind: task
status: open
priority: 3
version: 1
labels: []
dependencies: []
created_at: 2026-08-25T04:15:44.960Z
updated_at: 2026-08-25T04:15:44.960Z
---
chopdiff 0.4.0 requires flexdoc<0.4.0,>=0.3.0. That cap is what holds flexdoc at 0.3.0 in this project — not the supply-chain cool-off, since flexdoc is first-party and permanently exempt in [tool.uv.exclude-newer-package].

flexdoc 0.4.0 has been out since 2026-07-20 (requires-python >=3.11,<4.0) but cannot reach deep-transcribe, kash-media, kash-docs, or kash-shell while chopdiff caps it. Those three only ask for flexdoc>=0.3.0, so chopdiff is the sole blocker.

Fix is upstream in chopdiff (also jlevy): verify compatibility with flexdoc 0.4.x, widen the constraint to >=0.3.0,<0.5, and release. Then re-run the dependency refresh here to pick it up.

Found during the 2026-08-24 dependency refresh.
