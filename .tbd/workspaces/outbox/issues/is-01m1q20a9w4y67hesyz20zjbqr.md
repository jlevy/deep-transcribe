---
type: is
id: is-01m1q20a9w4y67hesyz20zjbqr
title: "PR #19 review R2: a --segments rerun re-runs the pipeline above the boundary"
kind: bug
status: closed
priority: 0
version: 5
spec_path: docs/project/specs/active/plan-2026-09-04-long-form-stabilization.md
labels: []
dependencies: []
parent_id: is-01m1q1zs4f81krjzenfbtmp35t
created_at: 2026-09-04T20:33:16.602Z
updated_at: 2026-09-04T22:29:16.046Z
closed_at: 2026-09-04T20:57:06.691Z
close_reason: Two causes fixed and measured; the third is a real design tension between sticky late inputs and cache identity, deferred to dt-xjlp rather than half-fixed.
resolution: null
duplicate_of: null
---
BLOCKING. Source item's persisted metadata changes shape between a plain run and a --segments run, and kash hashes the file on disk. Two causes: (a) strip_volatile_source_fields runs in memory but fetch_url_item_content already wrote counters to disk via ws.save(overwrite=True); run_transcription:518 only persists when apply_transcription_metadata changed something. (b) remove_segment_hints leaves an empty transcription: {} where an item that never had hints has no key at all. Evidence: dt-hintrerun.log re-ran correct_speaker_turns 31 min. Fix: have the strip report whether it removed anything and persist when it did; drop the transcription mapping when empty. Pin with a test comparing item.metadata() for both shapes.

## Notes

Two of three causes fixed and verified on a fresh workspace: view_count no longer reaches disk (persist when the strip removes something), and the emptied transcription mapping is pruned. Unchanged rerun is now 5 s with zero API calls, and a --segments rerun no longer re-runs speech-to-text or speaker correction.

Third cause NOT fixed, deferred to dt-xjlp with measurements: the late inputs are written back to the hashed resource on purpose (stickiness), so changing a hint still re-runs paragraph formatting and section headings. I briefly 'fixed' this by persisting a new_copy_with() clone, which regenerates created_at and therefore wrote different bytes every run — it invalidated the cache it meant to protect. Reverted.
