---
type: is
id: is-01m109e76rzkc4j2tqqf39r27h
title: Release Kash Docs without owning the Kash package initializer
kind: bug
status: closed
priority: 1
version: 6
labels: []
dependencies:
  - type: blocks
    target: is-01m109ec7nh773zjacw7szyvmq
parent_id: is-01m107tagtyzdrt6e727xfvxc8
created_at: 2026-08-27T00:20:40.278Z
updated_at: 2026-08-27T00:31:02.391Z
closed_at: 2026-08-27T00:31:02.389Z
close_reason: "Released Kash Docs 0.2.5 from merged PR #6 at 74c7d93b; local and CI gates passed, the published wheel omits kash/__init__.py while retaining kash.kits.docs, and a direct verified PyPI-wheel install imports Kash public APIs and FileStore without the install-order circular import."
resolution: null
duplicate_of: null
---
The kash-docs wheel ships a minimal kash/__init__.py that can overwrite the canonical kash-shell initializer according to install order, causing circular imports and loss of the Kash public API. Remove extension ownership of the top-level initializer, add a packaged-stack regression test, validate the wheel, and publish Kash Docs 0.2.5.
