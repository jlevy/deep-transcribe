---
type: is
id: is-01m1dbp059hmx278czczgmhjtm
title: Extract a concept map from transcripts
kind: feature
status: closed
priority: 2
version: 4
spec_path: docs/project/specs/active/plan-2026-08-31-transcript-timeline-and-concept-map.md
labels: []
dependencies:
  - type: blocks
    target: is-01m1dbp0gq7rdk8vaaqfnag9s7
parent_id: is-01m1dbmypatm5c5e8sbhzqmphd
created_at: 2026-09-01T02:09:59.976Z
updated_at: 2026-09-01T05:59:03.698Z
closed_at: 2026-09-01T05:59:03.697Z
close_reason: Concept extraction action, validation in the index builder, --concepts flag, and unit tests landed; live LLM run still to be exercised alongside the concept views
resolution: null
duplicate_of: null
---
Add src/deep_transcribe/concept_map.py: the concept schema (id, label, kind, gloss, mentions, span, speakers, relations), a closed relation vocabulary (leads-to, contrasts-with, elaborates, example-of, depends-on), and the extract_concepts action. Validate every mention timestamp against the index and drop unresolvable ones with a logged warning. Add the optional background-research pass behind the existing --web-search gate, preserving sources and provenance, with search results barred from introducing a concept the transcript did not establish. Merge concepts into the index before serialization. Add --concepts and set extract_concepts=True in TranscribeOptions.deep().
