---
type: is
id: is-01m1n0jtcf9ctz8wz8v4mq0b19
title: Highlight exact speaker and entity mentions in the summary
kind: task
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-09-03-dt-design-system-refactor.md
labels: []
dependencies: []
created_at: 2026-09-04T01:29:56.878Z
updated_at: 2026-09-04T01:34:15.684Z
closed_at: 2026-09-04T01:34:15.684Z
close_reason: Implemented and verified on the SNL test bed by capture and headless DOM checks; 100 tests and goldens green
resolution: null
duplicate_of: null
---
Exact matches in the summary prose are marked: speaker names take their speaker color, entity-kind concept labels are bolded. Matching is deliberately simple and robust: exact strings, longest-first, on non-word boundaries, applied to text nodes at runtime — exact matches always color correctly, fuzzier cases are out of scope.
