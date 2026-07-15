---
type: is
id: is-01kxj8kybch3y98k47rphvdw9v
title: Upgrade and release the dependency chain with patch versions
kind: task
status: closed
priority: 1
version: 1
labels: []
dependencies: []
parent_id: null
due_date: null
deferred_until: null
created_at: 2026-07-15T03:30:11.000Z
updated_at: 2026-07-15T05:03:36.000Z
closed_at: 2026-07-15T05:03:36.000Z
close_reason: All dependency releases are published as patch versions, downstream resolution is clean, and the published Deep Transcribe artifact passed its release smoke and local MP4 end-to-end run.
extensions:
  beads:
    original_id: dt-zeg.5
    imported_at: 2026-07-15T06:49:51.782Z
---
After local end-to-end validation, publish only required patch releases in dependency order and upgrade downstream constraints and locks through kash, kash-docs, kash-media, and Deep Transcribe.

## Notes

Published patch chain and validated released-only resolution: kash-shell 0.4.4 and 0.4.5, kash-docs 0.2.3, kash-media 0.4.3, and deep-transcribe 0.1.8. All release workflows passed. Global uv tool install resolves deep-transcribe 0.1.8 with kash-shell 0.4.5, kash-docs 0.2.3, and kash-media 0.4.3, with no workspace overrides or heavyweight optional document packages. The published CLI completed the annotated local MP4 regression and exported 19 valid frame references.
