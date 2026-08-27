---
type: is
id: is-01m109e76rzkc4j2tqqf39r27h
title: Release Kash Docs without owning the Kash package initializer
kind: bug
status: in_progress
priority: 1
version: 5
labels: []
dependencies:
  - type: blocks
    target: is-01m109ec7nh773zjacw7szyvmq
parent_id: is-01m107tagtyzdrt6e727xfvxc8
created_at: 2026-08-27T00:20:40.278Z
updated_at: 2026-08-27T00:20:57.727Z
---
The kash-docs wheel ships a minimal kash/__init__.py that can overwrite the canonical kash-shell initializer according to install order, causing circular imports and loss of the Kash public API. Remove extension ownership of the top-level initializer, add a packaged-stack regression test, validate the wheel, and publish Kash Docs 0.2.5.
