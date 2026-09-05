---
type: is
id: is-01m1qg4dq34m5rynfm9m94739m
title: Recipe-level text replacements applied after speech-to-text
kind: feature
status: open
priority: 2
version: 1
spec_path: docs/project/specs/active/plan-2026-09-04-agent-iteration-loop.md
labels: []
dependencies: []
parent_id: is-01m1qfkw8vxpzmyds5qsxm798b
created_at: 2026-09-05T00:40:11.234Z
updated_at: 2026-09-05T00:40:11.234Z
---
Measured on Lex #501 with 17 key terms passed to Deepgram (nova-3): Omarchy went from 4 to 47 and Amache from 14 to 0, but Omachi remained 19 (from 25) — keyterm boosting is not total, and the residue is in the transcript body where processing instructions cannot reach. Add a replacements: {Omachi: Omarchy, ...} mapping to --metadata, applied as a deterministic, case-preserving whole-word pass right after transcription (before speaker correction, so every later stage sees the corrected text). Changing it should re-run from that point, never speech-to-text. Report the count of replacements made. Refs the report's spelling-variant list, which is how an agent discovers what to put here.
