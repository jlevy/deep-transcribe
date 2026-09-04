---
type: is
id: is-01m1na58vampj3d053x9qddjf3
title: Keep word-level timings from speech-to-text
kind: feature
status: open
priority: 2
version: 1
spec_path: docs/project/specs/active/plan-2026-09-04-transcript-segments.md
labels: []
dependencies: []
parent_id: is-01m1n3q978x6fyhsyfm175ngy6
created_at: 2026-09-04T04:17:18.697Z
updated_at: 2026-09-04T04:17:18.697Z
---
Deepgram returns per-word timings including end times; the pipeline keeps only sentence start times. Retaining word timings would make inter-sentence gaps exact rather than estimated from an assumed speaking rate, which matters for corroborating segment boundaries (a music sting or edit point between segments shows as real silence). Measured on Lex #501: the teaser-to-intro boundary at 1:27 shows a ~17s estimated gap, among the largest in the episode, but comparable estimated gaps occur mid-conversation, so the estimate is too noisy to lean on alone.
