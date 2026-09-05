---
type: is
id: is-01m1q210kj03ase12b5kg7yj8q
title: "PR #19 review R6: no way to clear stored hints or instructions"
kind: bug
status: closed
priority: 2
version: 3
spec_path: docs/project/specs/active/plan-2026-09-04-long-form-stabilization.md
labels: []
dependencies: []
parent_id: is-01m1q1zs4f81krjzenfbtmp35t
created_at: 2026-09-04T20:33:39.440Z
updated_at: 2026-09-04T22:40:18.805Z
closed_at: 2026-09-04T22:40:18.804Z
close_reason: --segments none and --instructions none clear the stored value, verified on disk through run_transcription on a real workspace; a memory-only clear was shown to pass every unit test and fail only the disk test.
resolution: null
duplicate_of: null
---
Once --segments or --instructions has been stored on an item there is no CLI affordance to remove it; a user must hand-edit the resource YAML. Add an explicit clear (e.g. --segments none / --no-segments).
