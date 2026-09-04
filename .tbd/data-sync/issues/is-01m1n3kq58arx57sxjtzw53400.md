---
type: is
id: is-01m1n3kq58arx57sxjtzw53400
title: Validate and cap output scale for hours-long media
kind: task
status: open
priority: 0
version: 2
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T02:22:52.071Z
updated_at: 2026-09-04T02:44:37.947Z
---
Unvalidated at scale because the run never reached processing. Expect: frame captures at paragraph granularity produce hundreds to thousands of ffmpeg seeks and a very large assets directory; the concept cap of 24 may be low for five hours; the Timeline overview must stay legible with dozens of sections; per-concept tracks and the rail need checking at that density; and the single HTML plus PDF may become impractically large. Measure each, then cap or tier what needs it.
