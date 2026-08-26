---
type: is
id: is-01m0zw7p1cq8607eb675yape5m
title: Preserve frame assets when exporting resumed transcript stages
kind: bug
status: closed
priority: 1
version: 4
labels: []
dependencies: []
parent_id: is-01m0zvrk2pytbx4qsk4xfaa4nv
created_at: 2026-08-26T20:29:54.591Z
updated_at: 2026-08-26T23:37:09.840Z
closed_at: 2026-08-26T23:37:09.840Z
close_reason: Implemented upstream and in Deep Transcribe, validated with focused and full tests, committed and pushed, passed CI, and verified in the final browser-generated PDF.
---
A late-stage cached rerender must resolve frame assets deterministically. Frame insertion must also skip nested timestamp-icon spans and place each capture after the complete timestamp citation, never between its brackets. Cover spacing and placement with generic fixtures.
