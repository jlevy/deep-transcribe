---
type: is
id: is-01kxj5t1w964tpzxfx8eacf734
title: Prune unreferenced frame candidates from transcript exports
kind: bug
status: closed
priority: 2
version: 3
labels: []
dependencies: []
parent_id: is-01kxj4xxyfwmxmk3z9mebcf92x
created_at: 2026-07-15T06:00:46.216Z
updated_at: 2026-07-15T06:48:58.361Z
closed_at: 2026-07-15T06:48:58.361Z
close_reason: Implemented, validated end to end, merged, and released in the patch dependency chain ending with Deep Transcribe 0.1.9.
---
insert_frame_captures filters 44 candidates to 15 referenced frames but leaves and exports all 44 JPEGs. Remove rejected candidates or copy only referenced assets so annotated deliverables are not unnecessarily large.

## Notes

Implemented pruning of rejected similarity-filter frame candidates before export. Regression retains only selected paths. kash-media lint/type and 10 tests pass. SNL run exposed 44 captured candidates vs 15 HTML references before fix.
