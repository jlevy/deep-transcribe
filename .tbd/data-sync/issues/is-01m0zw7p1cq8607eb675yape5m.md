---
type: is
id: is-01m0zw7p1cq8607eb675yape5m
title: Preserve frame assets when exporting resumed transcript stages
kind: bug
status: open
priority: 1
version: 1
labels: []
dependencies: []
parent_id: is-01m0zvrk2pytbx4qsk4xfaa4nv
created_at: 2026-08-26T20:29:54.591Z
updated_at: 2026-08-26T20:29:54.591Z
---
A late-stage cached rerender can emit HTML that retains the source item's relative frame-asset path without materializing or linking that asset directory beside the export. Make HTML and PDF export resolve item assets deterministically without copying large media unnecessarily. Use generic fixtures only.
