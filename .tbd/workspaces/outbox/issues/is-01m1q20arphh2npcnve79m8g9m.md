---
type: is
id: is-01m1q20arphh2npcnve79m8g9m
title: "PR #19 review R3: frame-density cap strips 80% of frames from short media"
kind: bug
status: closed
priority: 0
version: 3
labels: []
dependencies: []
parent_id: is-01m1q1zs4f81krjzenfbtmp35t
created_at: 2026-09-04T20:33:17.077Z
updated_at: 2026-09-04T20:43:50.822Z
closed_at: 2026-09-04T20:43:50.820Z
close_reason: Floor on absolute frame count added alongside the density; the real showcase shape (15 frames over 4:26) is now untouched, verified to fail against the old target. Long-form thinning unchanged at ~240 of 502.
resolution: null
duplicate_of: null
---
BLOCKING. TARGET_FRAMES_PER_HOUR=45.0 documented as calibrated on 'the 22-minute example at about 41 frames an hour' — that example does not exist in the repo; it appears back-derived from the synthetic fixture in test_short_media_is_untouched. The real showcase (SNL Hotel Check In) is 4:26 with 15 frames = 231/hour, so thinning removes 12 of 15. Stated invariant 'short media never changes' is false. frame_density.py:24. Confirmed on disk: snl-showcase assets hold 3 files where the pre-PR run holds 15. Fix: add a floor (MIN_FRAMES ~12) or skip below a span; test with the real example's shape; regenerate docs/examples.
