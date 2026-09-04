---
type: is
id: is-01m1n3q978x6fyhsyfm175ngy6
title: Transcript segments with default suppression
kind: feature
status: open
priority: 1
version: 11
spec_path: docs/project/specs/active/plan-2026-09-04-transcript-segments.md
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
child_order_hints:
  - is-01m1n3w2gnfy82syecqepy5b93
  - is-01m1n3w35gh277jkr5rreywjsd
  - is-01m1n3w3s56t6zzyf0e8zbzcaq
  - is-01m1n3w54cw73gbx7zft0av37v
  - is-01m1n9pf2qwyfejb1xdjzx385k
  - is-01m1n9rj7r4bw9maq6wcggj6kz
  - is-01m1na58vampj3d053x9qddjf3
created_at: 2026-09-04T02:24:48.871Z
updated_at: 2026-09-04T04:17:18.697Z
---
MEASURED against Lex #501 (5.3h) before designing:
- 23 YouTube chapters with exact boundaries and human titles, including 'Episode highlight' (0:00-1:27) and 'Introduction' (1:27-2:56). Excellent free skeleton.
- NO chapter marks a sponsor; no chapter title contains any sponsor name.
- The description names 8 sponsors, but 5 never appear in the transcript, and the 3 that do are organic conversation (Shopify layoffs and its CTO, Perplexity and Plaud as products discussed).
- Searching the whole transcript for ad-read phrasing ('brought to you by', 'this episode is sponsored', 'use code') returns ZERO matches.
=> This episode has no in-audio sponsor reads despite naming 8 sponsors. Description metadata is not evidence an ad exists; name matching yields only false positives and would have suppressed real conversation.

DESIGN: segments partition the whole timeline; each states a purpose (content/preview/intro/sponsor/outro) and whether it is suppressed by default, with source recorded as chapter or detected. Chapters seed the partition where they exist; detection fills gaps and handles sources without chapters. Suppressed passages collapse in place, never delete. See plan-2026-09-04-transcript-segments.md.
