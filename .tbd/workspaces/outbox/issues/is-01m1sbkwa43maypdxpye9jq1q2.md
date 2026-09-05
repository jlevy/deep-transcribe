---
type: is
id: is-01m1sbkwa43maypdxpye9jq1q2
title: One grouping rule for long vs short recordings, with a control
kind: feature
status: closed
priority: 1
version: 2
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-05T17:59:43.683Z
updated_at: 2026-09-05T18:23:40.489Z
closed_at: 2026-09-05T18:23:40.488Z
close_reason: --grouping on|off|MINUTES (default 45) as an export setting in window.DT_GROUPING; model.grouped decided once in dt_core; count thresholds removed; docs row, skill line, tests. Verified in the browser; 6b8df94.
resolution: null
duplicate_of: null
---
Outline, Concepts, Claims, and the graph group by theme only when the recording is long enough (cutoff around 30-60 min). One heuristic, one place, and a flag to force it on or off.
