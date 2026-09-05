---
type: is
id: is-01m1n9pf2qwyfejb1xdjzx385k
title: Use publisher chapters as section headings
kind: feature
status: open
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-09-04-transcript-segments.md
labels: []
dependencies:
  - type: blocks
    target: is-01m1ng5b07vkx3hx5ghky3sxf5
parent_id: is-01m1qfsvgm7h96jcrcyv7k6mxg
created_at: 2026-09-04T04:09:13.558Z
updated_at: 2026-09-05T00:34:26.453Z
---
yt-dlp returns 23 human-written chapters with exact boundaries for Lex #501. The insert_section_headings stage currently pays a model to invent headings the publisher already stated, and does so less accurately. Where chapters exist, use them as the section structure; fall back to inference when they do not. Cheaper and better.
