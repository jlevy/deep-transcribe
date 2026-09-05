---
type: is
id: is-01m1q3by2vaj7zs9cct9xqpsem
title: Store analysis-only inputs outside the hashed metadata
kind: feature
status: open
priority: 2
version: 6
spec_path: docs/project/specs/active/plan-2026-09-04-long-form-stabilization.md
labels: []
dependencies: []
parent_id: is-01m1n3q978x6fyhsyfm175ngy6
created_at: 2026-09-04T20:57:05.882Z
updated_at: 2026-09-05T00:27:12.304Z
---
Segment hints and processing instructions stick to the item on purpose, so a later run without the flag still honors them — pinned by test_processing_instructions_bypass_raw_and_formatting_cache_identity, and the reason a clear affordance is needed at all. But they are stored in item.extra, which is part of the file kash hashes, so CHANGING one re-runs paragraph formatting and section headings.

MEASURED on a fresh workspace (3 passes, short source):
  pass 1 plain, first ever        96 s, 1 deepgram call
  pass 2 plain rerun               5 s, 0 deepgram, 0 stages      <- unchanged rerun is free
  pass 3 --segments added         62 s, 0 deepgram, 0 speaker correction,
                                  but break_into_paragraphs and insert_section_headings re-ran
On the 5h15m recording those two stages are 13 and 30 minutes.

Mechanism, from the recorded action inputs: the transcribe step's argument is
resources/watch_1.resource.yml@sha1:..., and the sha1 differs between a plain run
(6b7b99fa) and a --segments run (86b7c1d8) while the transcript bodies are byte-identical.
The finally block in transcribe_with_options writes the late inputs back to the resource,
so the hashed file carries them from then on.

Two ways out, neither small: keep the late inputs in a sidecar the hash does not cover, or
give kash a way to exclude named extra keys from an input hash. Do not solve it by dropping
the write-back — that is the stickiness feature, and removing it fails the test above.

Not a regression from PR #19: the unchanged-rerun property works and is the common case.
What does not hold is the claim that editing a hint is cheap.

## Notes

Final scope after measurement: only the FIRST application of hints to a workspace pays the ~45 min formatting rerun; every later edit resumes at the outline (20 min at scale). This is a one-time cost per source, not per iteration. Reprioritize accordingly; P2 is defensible.
