---
type: is
id: is-01m1p0rsvvp8ah3tczzv446xdc
title: Reduce pass times out on the maps that need it
kind: bug
status: closed
priority: 0
version: 2
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T10:52:27.386Z
updated_at: 2026-09-04T16:11:19.657Z
closed_at: 2026-09-04T16:11:19.656Z
close_reason: "Fixed by batching the reduce to 25 concepts per call. On the exact 119-concept map that timed out twice: 114 concepts in 13 themes, 0 unthemed, 249 s."
resolution: null
duplicate_of: null
---
The concept reduce pass times out at the size it is actually needed for.

MEASURED, same model (default_structured), same workspace:
  119 concepts   600 s timeout (twice), 267 s success (once)
  20 concepts    26 s, themed 19/19
A concept-EXTRACTION chunk is a comparable ~8k tokens of input and completes in about
43 s, so this is not about payload size. Numbering the concepts so the response echoes
"1, 4, 7" rather than full slugs cut the response 86% and changed nothing, which rules
out response length too.

What is left is the task. Organizing 119 items into themes is combinatorial in a way
extraction is not, and the cost looks superlinear in the number of items.

CONSEQUENCE, and why this matters more than a slow stage: when the pass fails there are
no themes, and the Concepts panel silently falls back to the flat list it was built to
replace — 14,901 px of it on the measured run. The broad exception handler means the run
survives, but surviving is not working. Treat the theming as undelivered until this is
fixed.

LIKELY FIX, pending the scaling numbers at 40 and 80: reduce in batches. Concepts arrive
in timeline order and themes are roughly contiguous, so batches of about 40 in that order
would each theme their own stretch, followed by a small consolidation pass over just the
theme LABELS to collapse near-duplicates between batches. That pass reads a dozen strings,
so it is cheap at any recording length.

The cost of batching is that dedup no longer sees the whole map at once. Most duplicates
come from adjacent extraction chunks, so timeline-ordered batches should still catch
them; overlapping the batches slightly would catch more.
