---
type: is
id: is-01m0zt07sqbdyrrmzzqekqwx75
title: Render local-media timestamps as muted plain text
kind: bug
status: closed
priority: 2
version: 3
labels: []
dependencies: []
parent_id: is-01m0zpq37wdhx51829qx0xmf0t
created_at: 2026-08-26T19:50:53.486Z
updated_at: 2026-08-26T20:17:22.105Z
closed_at: 2026-08-26T20:17:22.105Z
close_reason: Implemented, validated end-to-end, committed, pushed, and CI passed.
resolution: null
duplicate_of: null
---
Render transcript timestamps as muted bracketed text. Keep timestamp links only for supported web media URLs, and never emit unusable file-path links for local media. Cover local and web source behavior without placing private fixtures in the repository.
