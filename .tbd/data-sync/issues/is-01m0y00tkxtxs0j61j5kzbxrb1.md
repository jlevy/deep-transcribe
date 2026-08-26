---
type: is
id: is-01m0y00tkxtxs0j61j5kzbxrb1
title: Validate two-speaker correction from a cached transcript
kind: task
status: closed
priority: 1
version: 6
labels: []
dependencies: []
parent_id: is-01m0xwzrh7debayb7dhcrz1d9y
child_order_hints:
  - is-01m0y0n549e2aw23xm9aqmqdjy
created_at: 2026-08-26T02:57:35.354Z
updated_at: 2026-08-26T03:46:08.980Z
closed_at: 2026-08-26T03:46:08.979Z
close_reason: Implemented, regression-tested, and validated with real private and public end-to-end workflows.
resolution: null
duplicate_of: null
---
Use reusable private metadata with a complete two-person roster, rerun downstream processing without a second Deepgram request, and verify every speaker label.

## Notes

Validated a cached long-form two-person correction: all 1,931 timestamped utterances were preserved, only the two roster labels remained, and the Deepgram request count stayed at one through the semantic rerun.
