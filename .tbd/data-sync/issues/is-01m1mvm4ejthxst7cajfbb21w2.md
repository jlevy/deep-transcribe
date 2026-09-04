---
type: is
id: is-01m1mvm4ejthxst7cajfbb21w2
title: Fall back to direct YouTube links on file:// pages
kind: bug
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-31-transcript-timeline-and-concept-map.md
labels: []
dependencies: []
created_at: 2026-09-04T00:03:17.073Z
updated_at: 2026-09-04T00:13:58.233Z
closed_at: 2026-09-04T00:13:58.232Z
close_reason: "Implemented and verified on the SNL test bed: tooltip contract tested in-browser, file:// fallback verified headless with file access, palette AA-checked, print gate still green"
resolution: null
duplicate_of: null
---
YouTube embeds refuse to play (error 153) when the exported HTML is opened via file:// because no HTTP referer is sent. On file: protocol, bypass the popover interception entirely: timestamp links get target=_blank rel=noopener and a document-level capture handler stops propagation before the popover's per-anchor listener, so links open YouTube directly at the right timestamp. Served over http(s), the in-page popover keeps working unchanged.
