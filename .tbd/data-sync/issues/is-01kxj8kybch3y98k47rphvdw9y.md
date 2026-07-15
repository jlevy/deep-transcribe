---
type: is
id: is-01kxj8kybch3y98k47rphvdw9y
title: Add typed transcription context metadata to kash Item
kind: feature
status: closed
priority: 1
version: 1
labels: []
dependencies: []
parent_id: null
due_date: null
deferred_until: null
created_at: 2026-07-15T03:30:06.000Z
updated_at: 2026-07-15T04:28:08.000Z
closed_at: 2026-07-15T04:28:08.000Z
close_reason: Implemented persisted additional context, bounded prompt context, settings-aware transcription caching, metadata-sensitive sidematter hashing, binary reimport stability, and passing lint/tests.
extensions:
  beads:
    original_id: dt-zeg.1
    imported_at: 2026-07-15T06:49:51.799Z
---
Define persisted, YAML-serializable source metadata for additional context, key terms, and speaker hints; add a generic metadata enrichment operation; preserve source metadata through derived items without confusing it with transient ActionContext.

## Notes

Implementation branch codex/transcription-context created from current origin/main in all repositories. Designing top-level persisted metadata plus bounded prompt-context support.
