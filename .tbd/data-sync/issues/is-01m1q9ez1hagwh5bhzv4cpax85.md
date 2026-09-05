---
type: is
id: is-01m1q9ez1hagwh5bhzv4cpax85
title: Tests sharing a kash workspace name read each other's files
kind: bug
status: open
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-09-04-long-form-stabilization.md
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T22:43:36.624Z
updated_at: 2026-09-05T06:44:33.731Z
---
Found during the R11 revert check. kash registers workspaces by directory NAME, so every test that opens kash_runtime(tmp_path / 'workspace') resolves current_ws() to whichever 'workspace' registered first in the process, not its own tmp_path. Two of R11's tests initially passed against a reverted fix because they read a segments.suggested.yml a previous test had written into a shared stale dir. R11 fixed only its own tests (unique name ws-<tmp_path.name>, plus an assertion that current_ws().base_dir is the dir passed in).

The same pattern is used in tests/test_transcript_overview.py (_runtime helper), elsewhere in tests/test_transcribe_commands.py, and the inline tests in concept_map.py and transcription_metadata.py. Every one is exposed. Fix: one shared fixture that opens a uniquely named workspace and asserts it is current, used everywhere; then run the suite in random order to prove no test depends on another's leftovers. Seventh instance on this branch of a test passing for the wrong reason.

## Notes

Partially addressed: tests/conftest.py (from dt-i6mg's agent) isolates kash workspace registration per test and is load-bearing — without it a CLI test passes against a broken --export-only by re-exporting another test's workspace. The structural cause (run_transcription hardcodes 'workspace') remains.
