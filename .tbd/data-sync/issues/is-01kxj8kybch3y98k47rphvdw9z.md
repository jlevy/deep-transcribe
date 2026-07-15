---
type: is
id: is-01kxj8kybch3y98k47rphvdw9z
title: Context-aware transcription metadata across kash and Deep Transcribe
kind: epic
status: closed
priority: 1
version: 3
labels: []
dependencies: []
parent_id: is-01kxj4xxyfwmxmk3z9mebcf92x
due_date: null
deferred_until: null
created_at: 2026-07-15T03:30:05.000Z
updated_at: 2026-07-15T06:50:12.671Z
closed_at: 2026-07-15T06:50:12.670Z
close_reason: Historical context-metadata dependency effort completed and released through Deep Transcribe 0.1.9; retained under the canonical modernization epic.
extensions:
  beads:
    original_id: dt-zeg
    imported_at: 2026-07-15T06:49:51.805Z
---
Add persistent source-level context and structured transcription hints, make every relevant transcription and document action consume them correctly, preserve metadata through all pipelines, upgrade dependent packages, and validate quality on a short public video.

## Notes

Full effort completed. Published kash-shell 0.4.4/0.4.5, kash-docs 0.2.3, kash-media 0.4.3, and deep-transcribe 0.1.8. CI, lint, unit tests, skill validation, provider model checks, short YouTube quality review, raw-file correction rerun, visual HTML review, and published local MP4 frame-capture regression all passed. The globally installed deep-transcribe is 0.1.8; help startup is 0.10-0.14s and the default environment contains no Torch or document-processing extras.
