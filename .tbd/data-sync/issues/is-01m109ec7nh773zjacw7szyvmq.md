---
type: is
id: is-01m109ec7nh773zjacw7szyvmq
title: Release Kash Media without owning the Kash package initializer
kind: bug
status: open
priority: 1
version: 1
labels: []
dependencies: []
parent_id: is-01m107tagtyzdrt6e727xfvxc8
created_at: 2026-08-27T00:20:45.429Z
updated_at: 2026-08-27T00:20:45.429Z
---
The kash-media wheel also ships a minimal kash/__init__.py and can overwrite the canonical kash-shell initializer. Remove extension ownership of the top-level initializer, preserve the implicit namespace payload, require the fixed Kash Docs release, add packaged-stack regression coverage, and publish Kash Media 0.4.6.
