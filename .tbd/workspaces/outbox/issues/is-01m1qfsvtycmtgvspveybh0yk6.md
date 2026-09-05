---
type: is
id: is-01m1qfsvtycmtgvspveybh0yk6
title: Fold back-channel turns into the surrounding paragraph
kind: feature
status: open
priority: 1
version: 1
spec_path: docs/project/specs/active/plan-2026-09-04-long-form-stabilization.md
labels: []
dependencies: []
parent_id: is-01m1qfkw8vxpzmyds5qsxm798b
created_at: 2026-09-05T00:34:25.245Z
updated_at: 2026-09-05T00:34:25.245Z
---
Measured on Lex #501: 498 paragraphs consist of 'Mhmm.' alone, plus many 'Yeah.', 'Right.', 'So' one-word turns (e.g. 313.84 DHH 'Mhmm. Everything turned…', 314.77 DHH 'So'). Each renders as its own speaker turn with its own timestamp, so the transcript is ~1,300 turns of which hundreds carry no content. normalize_transcript_fragments (step05) does not catch them.

Add a normalization option, on by default for --formatted and above, that folds a turn whose text is only a back-channel token (configurable list: mhmm, mm-hmm, uh-huh, yeah, right, okay, sure, so) into the previous speaker's paragraph as a bracketed aside or drops it, preserving the citation of the substantive turn. Expose --keep-backchannel to disable. Measure before/after turn counts on the full export.
