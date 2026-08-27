---
type: is
id: is-01m107q73p72w6xhebb6jr66tv
title: Release Kash 0.4.7
kind: task
status: closed
priority: 1
version: 5
labels: []
dependencies:
  - type: blocks
    target: is-01m107q7cbhybbteyqfxg4esyq
parent_id: is-01m107tagtyzdrt6e727xfvxc8
created_at: 2026-08-26T23:50:37.935Z
updated_at: 2026-08-26T23:58:54.281Z
closed_at: 2026-08-26T23:58:54.267Z
close_reason: Released kash-shell 0.4.7 from merged main; local lint/type and 315 tests passed, the wheel/sdist built and installed in isolation, GitHub publish workflow passed, PyPI hashes were verified, and the published `kash --version` reported 0.4.7.
resolution: null
duplicate_of: null
---
Release the merged timestamp and transcript-boundary fixes from current main as kash-shell 0.4.7. Run local and remote gates, publish through the tag workflow, verify PyPI metadata, and smoke-test the installed wheel.
