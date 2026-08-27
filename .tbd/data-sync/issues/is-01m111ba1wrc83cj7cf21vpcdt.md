---
type: is
id: is-01m111ba1wrc83cj7cf21vpcdt
title: Expose bounded channel and discovery metadata through Kash
kind: feature
status: in_progress
priority: 2
version: 3
labels: []
dependencies:
  - type: blocks
    target: is-01m111bhjv1epzw4m0tbs9b84p
parent_id: is-01m1118hwdhra16fmaz6jd1smt
created_at: 2026-08-27T07:18:30.715Z
updated_at: 2026-08-27T07:42:16.091Z
---
Add reusable optional channel/uploader, category, and tag fields to Kash media metadata and YouTube extraction, release compatible Kash packages if needed, then consume the released fields in Deep Transcribe prompts.

## Notes

Core field preservation is committed at jlevy/kash#21 with green CI. YouTube mapping is committed at draft jlevy/kash-media#11, which waits for the kash-shell patch release and dependency-floor update.
