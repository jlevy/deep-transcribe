---
type: is
id: is-01m10nvfk97hjch3pn9q6xvx0g
title: Make natural-language context the primary CLI interface
kind: feature
status: closed
priority: 1
version: 5
labels: []
dependencies: []
parent_id: is-01m10kjrzedwht5b4mqbmwm3yp
created_at: 2026-08-27T03:57:37.768Z
updated_at: 2026-08-27T04:27:15.822Z
closed_at: 2026-08-27T04:27:15.821Z
close_reason: "Implemented and committed in 3845021; PR #13 is open and all CI checks pass."
resolution: null
duplicate_of: null
---
Let users describe participants, roles, ordering, terminology, and desired output in ordinary prose. Route that prose through the LLM-backed speaker and overview stages, preserve it for cache-aware reruns, and keep structured metadata only as an optional exact override and automation surface. Simplify the public hotel example accordingly.

## Notes

The prose-first CLI and documentation are implemented and committed in 3845021. Human-facing examples use ordinary --context and --instructions prose, with structured metadata retained for automation and exact overrides. Live cached hotel validation inferred both speaker labels without another Deepgram request. Local gates and PR #13 CI pass.
