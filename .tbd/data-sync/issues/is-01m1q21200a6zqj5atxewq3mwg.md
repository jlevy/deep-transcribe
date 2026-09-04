---
type: is
id: is-01m1q21200a6zqj5atxewq3mwg
title: "PR #19 review R9: reduce batches are not told they see one stretch"
kind: bug
status: open
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-09-04-long-form-stabilization.md
labels: []
dependencies: []
parent_id: is-01m1q1zs4f81krjzenfbtmp35t
created_at: 2026-09-04T20:33:40.862Z
updated_at: 2026-09-04T22:29:16.046Z
---
The batched reduce prompt does not say the batch is a window into a longer recording, so the model names themes as if each batch were the whole thing. Add that framing to the per-batch prompt.
