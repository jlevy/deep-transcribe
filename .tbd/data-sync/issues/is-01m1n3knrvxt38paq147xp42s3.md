---
type: is
id: is-01m1n3knrvxt38paq147xp42s3
title: "Long-form scale: make hours-long media work end to end"
kind: epic
status: open
priority: 1
version: 22
labels: []
dependencies: []
child_order_hints:
  - is-01m1n3kp47xvjpgapq51syjb7b
  - is-01m1n3kpfatq1ywx1k86vhsmd2
  - is-01m1n3kpt8rkxq4xa2hq48afzy
  - is-01m1n3kq58arx57sxjtzw53400
  - is-01m1n3q978x6fyhsyfm175ngy6
  - is-01m1n53d3bmpb1e479ans2y953
  - is-01m1n6gctkkxnqy75w1z619mfs
  - is-01m1n7c8d8yvrhkejcfjtva5r3
  - is-01m1n945s0m25334ssbw9gfwqe
  - is-01m1nax66j442h166dee52zt3r
  - is-01m1ng4k98ct0rh0aez0f65mq1
  - is-01m1ng5apmffpyrmqedmf8nk2v
  - is-01m1ng5b07vkx3hx5ghky3sxf5
  - is-01m1ngetsvzhmab7zqmh2c0259
  - is-01m1ngmw5rmvw53737am2ys73t
  - is-01m1nj101r8h6c0qjqjngbcw66
  - is-01m1nn9te3sc73grm9rarwq55h
  - is-01m1nwtknp04qqvtpdghs0342s
  - is-01m1nyv8q14zgfe1wypmpf6443
  - is-01m1p0rsvvp8ah3tczzv446xdc
created_at: 2026-09-04T02:22:50.649Z
updated_at: 2026-09-04T10:52:27.386Z
---
A 5.3-hour podcast (Lex Fridman #501, 18951s) exposed scale problems in download and transcription. Three upstream bugs found and fixed, each visible only by running at this scale.

MEASURED, run 1 (before fixes) vs run 3 (after):
  run 1: 13 GB pulled, ffmpeg pinned at 414% CPU for 45+ min still transcoding, never reached transcription
  run 3: 1.8 GB merged mp4 (f137 H.264 + f140 AAC), zero transcoding, download AND merge complete in 5 min 33 s

Fixes: kash #23 (TranscriptionLimits — request budget scales with duration), kash-media #12 (remux instead of re-encode; prefer H.264 over Premium VP9; VideoDownloadOptions control surface).

Remaining: output quality and legibility at this scale (dt-sfoz), and non-interview segment handling (dt-vkmf).
