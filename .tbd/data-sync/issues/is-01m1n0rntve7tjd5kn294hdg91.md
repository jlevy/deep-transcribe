---
type: is
id: is-01m1n0rntve7tjd5kn294hdg91
title: Timeline clicks always play, never scroll
kind: task
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-09-03-dt-design-system-refactor.md
labels: []
dependencies: []
created_at: 2026-09-04T01:33:08.826Z
updated_at: 2026-09-04T01:34:15.730Z
closed_at: 2026-09-04T01:34:15.730Z
close_reason: Implemented and verified on the SNL test bed by capture and headless DOM checks; 100 tests and goldens green
resolution: null
duplicate_of: null
---
Every click on a time position — Timeline sections, speaker band segments, the axis background, and the vertical rail — opens the video at that moment via playAt. No timeline click scrolls the document any more; scrolling remains only playAt's fallback when no linkable video exists, and the rail's keyboard turn-stepping.
