---
type: is
id: is-01m1q210kj03ase12b5kg7yj8q
title: "PR #19 review R6: no way to clear stored hints or instructions"
kind: bug
status: open
priority: 2
version: 1
labels: []
dependencies: []
parent_id: is-01m1q1zs4f81krjzenfbtmp35t
created_at: 2026-09-04T20:33:39.440Z
updated_at: 2026-09-04T20:33:39.440Z
---
Once --segments or --instructions has been stored on an item there is no CLI affordance to remove it; a user must hand-edit the resource YAML. Add an explicit clear (e.g. --segments none / --no-segments).
