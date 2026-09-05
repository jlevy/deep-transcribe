---
type: is
id: is-01m1qdyhy7011j40jc6xejs5kh
title: Frame thinning undershoots its target on real spacing
kind: task
status: open
priority: 3
version: 1
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-05T00:02:01.797Z
updated_at: 2026-09-05T00:02:01.797Z
---
frame_density.py says a five-hour recording 'lands near 240 rather than 502'. Measured twice on Lex #501: 1,442 captured, 944 filtered as similar, 498 into thinning, target max(20, 45/h x 5.26 h) = 237, kept 168 (morning) and 173 (evening). The nearest-ideal-moment picker with a floor gap of span/target/2 rejects picks when two ideal moments land nearest the same frame, which real (clustered) spacing does often; the uniform-spacing test does not exercise it. Either accept ~170 and say so, or let a rejected pick fall to the next-nearest unclaimed frame. Docstring corrected to the measured number in the same commit that filed this.
