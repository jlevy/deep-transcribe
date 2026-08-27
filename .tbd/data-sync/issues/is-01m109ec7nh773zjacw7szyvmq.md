---
type: is
id: is-01m109ec7nh773zjacw7szyvmq
title: Release Kash Media without owning the Kash package initializer
kind: bug
status: closed
priority: 1
version: 5
labels: []
dependencies:
  - type: blocks
    target: is-01m107q7x6bxhqwhqqgg10hx6j
parent_id: is-01m107tagtyzdrt6e727xfvxc8
created_at: 2026-08-27T00:20:45.429Z
updated_at: 2026-08-27T00:57:26.083Z
closed_at: 2026-08-27T00:57:26.075Z
close_reason: Released and verified kash-media 0.4.6; published wheel excludes kash/__init__.py, depends on kash-docs 0.2.6, repairs the reproduced 0.4.5 upgrade failure, and imports against kash-shell 0.4.8.
resolution: null
duplicate_of: null
---
The kash-media wheel also ships a minimal kash/__init__.py and can overwrite the canonical kash-shell initializer. Remove extension ownership of the top-level initializer, preserve the implicit namespace payload, require the fixed Kash Docs release, add packaged-stack regression coverage, and publish Kash Media 0.4.6.
