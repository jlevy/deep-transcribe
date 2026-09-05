---
type: is
id: is-01m1q21200a6zqj5atxewq3mwg
title: "PR #19 review R9: reduce batches are not told they see one stretch"
kind: bug
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-09-04-long-form-stabilization.md
labels: []
dependencies: []
parent_id: is-01m1q1zs4f81krjzenfbtmp35t
created_at: 2026-09-04T20:33:40.862Z
updated_at: 2026-09-04T22:37:16.203Z
closed_at: 2026-09-04T22:37:16.201Z
close_reason: Each reduce batch is told it is one stretch of N with its clock range and a per-stretch theme budget; a single-batch map keeps whole-recording framing. Test captures the prompt at the LLM boundary and was verified to fail against the old prompt.
resolution: null
duplicate_of: null
---
The batched reduce prompt does not say the batch is a window into a longer recording, so the model names themes as if each batch were the whole thing. Add that framing to the per-batch prompt.
