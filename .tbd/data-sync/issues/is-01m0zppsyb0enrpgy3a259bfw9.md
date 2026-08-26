---
type: is
id: is-01m0zppsyb0enrpgy3a259bfw9
title: Simplify timestamp citations in printed transcripts
kind: task
status: closed
priority: 2
version: 7
labels: []
dependencies: []
parent_id: is-01m0zpq37wdhx51829qx0xmf0t
created_at: 2026-08-26T18:53:18.665Z
updated_at: 2026-08-26T23:37:09.827Z
closed_at: 2026-08-26T23:37:09.827Z
close_reason: Implemented upstream and in Deep Transcribe, validated with focused and full tests, committed and pushed, passed CI, and verified in the final browser-generated PDF.
resolution: null
duplicate_of: null
---
Render bracketed timestamps in print at 8pt sans-serif, using one consistent light-gray color for the brackets and timestamp text. Keep the clock glyph and theme control hidden.

## Notes

Reopened: Expanded print acceptance criteria: 8pt single-light-gray timestamps with no trailing gap, plus regression coverage for nested timestamp spans around frame captures.
