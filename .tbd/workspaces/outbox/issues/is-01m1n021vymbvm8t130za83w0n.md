---
type: is
id: is-01m1n021vymbvm8t130za83w0n
title: Main text blocks are never gray
kind: task
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-09-03-dt-design-system-refactor.md
labels: []
dependencies: []
created_at: 2026-09-04T01:20:47.485Z
updated_at: 2026-09-04T01:34:15.645Z
closed_at: 2026-09-04T01:34:15.643Z
close_reason: Implemented and verified on the SNL test bed by capture and headless DOM checks; 100 tests and goldens green
resolution: null
duplicate_of: null
---
The summary inherited kash's gray .description color on web and print. Main text blocks (summary, glosses, transcript, outline) always render in --dt-text; gray is reserved for supporting labels and bracketed timestamps. Rule added to the tokens documentation.
