---
type: is
id: is-01m10nvfk97hjch3pn9q6xvx0g
title: Make natural-language context the primary CLI interface
kind: feature
status: in_progress
priority: 1
version: 2
labels: []
dependencies: []
parent_id: is-01m10kjrzedwht5b4mqbmwm3yp
created_at: 2026-08-27T03:57:37.768Z
updated_at: 2026-08-27T04:05:20.105Z
---
Let users describe participants, roles, ordering, terminology, and desired output in ordinary prose. Route that prose through the LLM-backed speaker and overview stages, preserve it for cache-aware reruns, and keep structured metadata only as an optional exact override and automation surface. Simplify the public hotel example accordingly.

## Notes

Confirmed the existing speaker-identification action already converts ordinary prose plus transcript content into a structured JSON speaker-ID mapping. Reoriented CLI help around --context/--context-file, added schema-free --title and --description flags, demoted YAML/JSON to optional automation overrides, replaced the README hotel YAML with prose flags, and updated the packaged guide and context design. A live cached hotel check inferred Hotel Receptionist and Tom Sanders from prose alone; Deepgram request count remained 1. Lint, type checking, Flowmark, and all 60 tests pass. Changes remain uncommitted with the sample artifacts pending user approval.
