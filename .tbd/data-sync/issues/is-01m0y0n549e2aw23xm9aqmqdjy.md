---
type: is
id: is-01m0y0n549e2aw23xm9aqmqdjy
title: Resolve overlap disagreements in long speaker correction
kind: bug
status: closed
priority: 1
version: 4
labels: []
dependencies: []
parent_id: is-01m0y00tkxtxs0j61j5kzbxrb1
created_at: 2026-08-26T03:08:41.480Z
updated_at: 2026-08-26T03:46:09.024Z
closed_at: 2026-08-26T03:46:09.024Z
close_reason: Implemented, regression-tested, and validated with real private and public end-to-end workflows.
resolution: null
duplicate_of: null
---
Long transcripts are processed in overlapping LLM windows. Reconcile disputed overlap utterances without silently choosing an inconsistent label, cover the behavior with tests, and rerun the cached end-to-end workflow.

## Notes

Root cause confirmed: adjacent overlapping correction windows can return different valid roster labels for the same boundary utterance. Added a focused third-pass adjudication using candidate labels, provider IDs, stable neighboring assignments, and source context; it remains fail-closed on uncertainty. The real long-form cached rerun resolved one conflict and preserved all timestamped utterances.
