---
type: is
id: is-01m1dbnk0wazn3pteq5k08jppx
title: Verify the printed PDF is unchanged by the new view
kind: task
status: closed
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-08-31-transcript-timeline-and-concept-map.md
labels: []
dependencies: []
parent_id: is-01m1dbmypatm5c5e8sbhzqmphd
created_at: 2026-09-01T02:09:46.523Z
updated_at: 2026-09-01T05:54:25.850Z
closed_at: 2026-09-01T05:54:25.849Z
close_reason: Automated print parity verified (8 pages both, pages 1 and 4 pixel-identical to the committed SNL PDF); manual QA steps added to the e2e runbook
resolution: null
duplicate_of: null
---
Re-print the example and compare against docs/examples/snl-hotel-check-in-transcript.pdf. Any visual difference in printed output is a defect in this feature. Add the print check to tests/e2e-test.runbook.md alongside manual QA for rail tracking, hover, click-to-scroll, connector drawing at several widths, light and dark themes, popover coexistence, keyboard nav, and prefers-reduced-motion.
