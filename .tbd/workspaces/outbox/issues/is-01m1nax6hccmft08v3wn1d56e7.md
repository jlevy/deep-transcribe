---
type: is
id: is-01m1nax6hccmft08v3wn1d56e7
title: Plan chunks by duration, snapped to sections
kind: feature
status: open
priority: 0
version: 1
spec_path: docs/project/specs/active/plan-2026-09-04-chunked-extraction.md
labels: []
dependencies: []
parent_id: is-01m1nax66j442h166dee52zt3r
created_at: 2026-09-04T04:30:22.763Z
updated_at: 2026-09-04T04:30:22.763Z
---
Group sections into chunks targeting a configurable duration (~30-60 min of audio), snapping boundaries to section edges so no chunk starts or ends mid-topic. A section longer than the target becomes its own chunk rather than being split. Time sets the call budget (5-10 calls for 5h, 12-24 for 12h); sections set the cut.
