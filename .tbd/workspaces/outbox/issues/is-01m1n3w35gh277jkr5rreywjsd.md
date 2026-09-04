---
type: is
id: is-01m1n3w35gh277jkr5rreywjsd
title: Add the detect_segments pass
kind: feature
status: open
priority: 2
version: 5
spec_path: docs/project/specs/active/plan-2026-09-04-long-form-stabilization.md
labels: []
dependencies: []
parent_id: is-01m1n3q978x6fyhsyfm175ngy6
created_at: 2026-09-04T02:27:26.511Z
updated_at: 2026-09-04T22:29:17.868Z
---
An LLM stage over the full transcript that proposes non-conversation spans, citing citation keys the way concept mentions do so every proposal traces to real timestamps; unresolvable proposals are dropped. Writes the exclusion file and changes nothing else. Exposed as --detect-segments, reporting what it found and the total time proposed.

## Notes

PARTIAL. What exists is _suggest_segments in transcribe_commands.py: a heuristic that detects the opening teaser by paragraph repetition and writes segments.suggested.yml. It is not an LLM stage, does not cite citation keys, is not exposed as --detect-segments, and finds only the opening clip — no ads, outros, or mid-recording spans. The bead's full scope remains open. Review R11 (dt-72oh) is fixing the re-offer bug in the heuristic that does exist.
