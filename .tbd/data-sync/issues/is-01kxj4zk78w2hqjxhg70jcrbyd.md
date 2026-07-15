---
type: is
id: is-01kxj4zk78w2hqjxhg70jcrbyd
title: Recover speaker turns when provider diarization merges distinct voices
kind: bug
status: closed
priority: 1
version: 5
labels: []
dependencies:
  - type: blocks
    target: is-01kxj4zkw8vp8g4ebs496hwdgw
parent_id: is-01kxj4xxyfwmxmk3z9mebcf92x
created_at: 2026-07-15T05:46:19.239Z
updated_at: 2026-07-15T06:48:58.338Z
closed_at: 2026-07-15T06:48:58.337Z
close_reason: Implemented, validated end to end, merged, and released in the patch dependency chain ending with Deep Transcribe 0.1.9.
---
Add a Deep Transcribe-owned correction path that accepts a known speaker roster plus source metadata, reassigns every timestamped ASR fragment to an exact roster label with a careful modern LLM, preserves transcript text/timestamps, and supports downstream-only reruns.

## Notes

Implemented and E2E-validated Deep-owned speaker_roster correction on SNL Hotel Check In: Nova-3/latest returned two provider IDs, while the careful profile reassigned 104 timestamped utterances across five exact roles. Verbatim timestamp spans preserved; explicit context cues resolved brief ambiguous transitions. Deep lint/type and 14 tests pass.
