---
type: is
id: is-01m1n18z4zn8q23tbrxxb2pn3z
title: Concept graph fits the printed page
kind: feature
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-09-03-dt-design-system-refactor.md
labels: []
dependencies: []
created_at: 2026-09-04T01:42:02.653Z
updated_at: 2026-09-04T01:45:40.663Z
closed_at: 2026-09-04T01:45:40.661Z
close_reason: "Verified against the regenerated 14-page SNL PDF: graph fits the page, breaks land cleanly, relations styled, examples refreshed from a real pipeline run"
resolution: null
duplicate_of: null
---
The graph's chips are absolutely positioned in screen pixels, so they overflowed the PDF page (headless printing never fires beforeprint). The panel now renders two layouts deterministically — the screen graph and a second at --dt-print-width — and CSS shows whichever medium applies, so printing needs no events at all.
