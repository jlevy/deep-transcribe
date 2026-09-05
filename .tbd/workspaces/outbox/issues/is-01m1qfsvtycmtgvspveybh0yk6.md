---
type: is
id: is-01m1qfsvtycmtgvspveybh0yk6
title: Fold back-channel turns into the surrounding paragraph
kind: feature
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-09-04-agent-iteration-loop.md
labels: []
dependencies: []
parent_id: is-01m1qfkw8vxpzmyds5qsxm798b
created_at: 2026-09-05T00:34:25.245Z
updated_at: 2026-09-05T06:38:30.438Z
closed_at: 2026-09-05T06:38:30.436Z
close_reason: "Back-channel turns fold into the previous paragraph as an attributed aside, between break_into_paragraphs and backfill_timestamps (the only window where the fold removes the chip rather than leaving it). Measured on the real 1,315-turn doc: 357 folds, turns 1,315 -> 958. --keep-backchannel disables. Four revert probes fail as expected, including one that moves the stage after backfill."
resolution: null
duplicate_of: null
---
Measured on Lex #501: 498 paragraphs consist of 'Mhmm.' alone, plus many 'Yeah.', 'Right.', 'So' one-word turns (e.g. 313.84 DHH 'Mhmm. Everything turned…', 314.77 DHH 'So'). Each renders as its own speaker turn with its own timestamp, so the transcript is ~1,300 turns of which hundreds carry no content. normalize_transcript_fragments (step05) does not catch them.

Add a normalization option, on by default for --formatted and above, that folds a turn whose text is only a back-channel token (configurable list: mhmm, mm-hmm, uh-huh, yeah, right, okay, sure, so) into the previous speaker's paragraph as a bracketed aside or drops it, preserving the citation of the substantive turn. Expose --keep-backchannel to disable. Measure before/after turn counts on the full export.
