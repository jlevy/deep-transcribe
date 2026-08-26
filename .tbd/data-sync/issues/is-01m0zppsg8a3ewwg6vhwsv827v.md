---
type: is
id: is-01m0zppsg8a3ewwg6vhwsv827v
title: Prevent restored timestamps from splitting transcript sentences
kind: bug
status: closed
priority: 1
version: 3
labels: []
dependencies: []
parent_id: is-01m0zpq37wdhx51829qx0xmf0t
created_at: 2026-08-26T18:53:18.205Z
updated_at: 2026-08-26T20:17:22.087Z
closed_at: 2026-08-26T20:17:22.087Z
close_reason: Implemented, validated end-to-end, committed, pushed, and CI passed.
resolution: null
duplicate_of: null
---
Investigate timestamp backfilling that inserts citations mid-sentence or adjacent to isolated words. Fix at the correct Deep Transcribe or Kash Media layer, test against a local dependency checkout, and keep private transcript details out of repository records.
