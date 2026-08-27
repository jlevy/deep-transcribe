---
type: is
id: is-01m10nvfk97hjch3pn9q6xvx0g
title: Make natural-language context the primary CLI interface
kind: feature
status: in_progress
priority: 1
version: 3
labels: []
dependencies: []
parent_id: is-01m10kjrzedwht5b4mqbmwm3yp
created_at: 2026-08-27T03:57:37.768Z
updated_at: 2026-08-27T04:08:13.792Z
---
Let users describe participants, roles, ordering, terminology, and desired output in ordinary prose. Route that prose through the LLM-backed speaker and overview stages, preserve it for cache-aware reruns, and keep structured metadata only as an optional exact override and automation surface. Simplify the public hotel example accordingly.

## Notes

The prose-first CLI and documentation are implemented. Human-facing examples now use one --context value containing ordinary sentences and one --instructions value; repeatable flags remain available only for script composition. Live cached hotel validation inferred the correct two speaker labels from prose without another Deepgram request. Lint, type checking, Flowmark, and all 60 tests pass. Changes remain uncommitted with the sample artifacts pending user approval.
