---
type: is
id: is-01m1t2j81wsj83qgxsvrkmyg3y
title: "tbd housekeeping: clear the outbox workspace, refresh stale managed skill files, confirm git auth for sync"
kind: task
status: closed
priority: 1
version: 2
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-06T00:40:47.419Z
updated_at: 2026-09-06T00:56:11.436Z
closed_at: 2026-09-06T00:56:11.435Z
close_reason: "tbd 0.8.1 is the latest; setup --auto retired the checked-in outbox workspace (174 issues, all present in tbd-sync: 313 there, 0 missing) and refreshed the managed skill files; doctor clean; sync pushes over SSH (git@github.com) with no credential override. Committed as 4364aa7."
resolution: null
duplicate_of: null
---
tbd status lists an 'outbox' workspace; doctor flags stale managed skill files (.agents/skills/tbd, .claude/skills/tbd). Latest tbd is 0.8.1 (installed). Sync must push without a credential-helper override.
