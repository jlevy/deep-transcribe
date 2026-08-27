---
type: is
id: is-01m10a69rjt2p1aby2a47tfq1h
title: Release Kash Docs 0.2.6 against Kash 0.4.8
kind: task
status: closed
priority: 1
version: 4
labels: []
dependencies:
  - type: blocks
    target: is-01m109ec7nh773zjacw7szyvmq
parent_id: is-01m107tagtyzdrt6e727xfvxc8
created_at: 2026-08-27T00:33:49.329Z
updated_at: 2026-08-27T00:51:11.344Z
closed_at: 2026-08-27T00:51:11.343Z
close_reason: Released and verified kash-docs 0.2.6 with kash-shell 0.4.8 floor; clean wheel ownership and upgrade from 0.2.4/0.4.7 both passed.
resolution: null
duplicate_of: null
---
Raise the Kash Docs kash-shell floor to 0.4.8 so an in-place extension upgrade reinstalls the canonical initializer after older overlapping wheels are removed. Revalidate initializer ownership, publish 0.2.6, and verify both fresh and upgrade-shaped installs.
