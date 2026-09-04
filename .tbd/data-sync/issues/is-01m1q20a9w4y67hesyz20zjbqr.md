---
type: is
id: is-01m1q20a9w4y67hesyz20zjbqr
title: "PR #19 review R2: a --segments rerun re-runs the pipeline above the boundary"
kind: bug
status: open
priority: 0
version: 1
labels: []
dependencies: []
parent_id: is-01m1q1zs4f81krjzenfbtmp35t
created_at: 2026-09-04T20:33:16.602Z
updated_at: 2026-09-04T20:33:16.602Z
---
BLOCKING. Source item's persisted metadata changes shape between a plain run and a --segments run, and kash hashes the file on disk. Two causes: (a) strip_volatile_source_fields runs in memory but fetch_url_item_content already wrote counters to disk via ws.save(overwrite=True); run_transcription:518 only persists when apply_transcription_metadata changed something. (b) remove_segment_hints leaves an empty transcription: {} where an item that never had hints has no key at all. Evidence: dt-hintrerun.log re-ran correct_speaker_turns 31 min. Fix: have the strip report whether it removed anything and persist when it did; drop the transcription mapping when empty. Pin with a test comparing item.metadata() for both shapes.
