---
type: is
id: is-01m1q21088xtxzhr4ez1006jhp
title: "PR #19 review R5: processing instructions are dropped in the synopsis reduce"
kind: bug
status: closed
priority: 1
version: 3
labels: []
dependencies: []
parent_id: is-01m1q1zs4f81krjzenfbtmp35t
created_at: 2026-09-04T20:33:39.080Z
updated_at: 2026-09-04T20:46:40.630Z
closed_at: 2026-09-04T20:46:40.628Z
close_reason: Removed the new_copy_with that overwrote the prepared body; test verified to fail without the fix.
resolution: null
duplicate_of: null
---
transcript_overview.py — the reduce step of the synopsis does not carry processing_instructions, so user instructions are honored per-chunk then lost when the chunks are combined.
