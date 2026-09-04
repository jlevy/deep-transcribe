---
type: is
id: is-01m1n049x3q6he9c4ey4emtvcb
title: Uniform timestamp hover and placement by speaker name
kind: task
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-09-03-dt-design-system-refactor.md
labels: []
dependencies: []
created_at: 2026-09-04T01:22:01.242Z
updated_at: 2026-09-04T01:34:15.653Z
closed_at: 2026-09-04T01:34:15.653Z
close_reason: Implemented and verified on the SNL test bed by capture and headless DOM checks; 100 tests and goldens green
resolution: null
duplicate_of: null
---
Timestamps never underline on hover anywhere (the transcript citations' inner links were picking up an underline the chips lacked), and each transcript citation moves up to sit beside the speaker's name on the label line, at normal weight. Continuation paragraphs without a label keep their trailing citation.
