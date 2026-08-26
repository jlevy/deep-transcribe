---
type: is
id: is-01m0zt07sqbdyrrmzzqekqwx75
title: Render local-media timestamps as muted plain text
kind: bug
status: closed
priority: 2
version: 7
labels: []
dependencies: []
parent_id: is-01m0zpq37wdhx51829qx0xmf0t
created_at: 2026-08-26T19:50:53.486Z
updated_at: 2026-08-26T23:37:09.834Z
closed_at: 2026-08-26T23:37:09.834Z
close_reason: Implemented upstream and in Deep Transcribe, validated with focused and full tests, committed and pushed, passed CI, and verified in the final browser-generated PDF.
resolution: null
duplicate_of: null
---
Render local-media timestamps as muted bracketed plain text with no unusable file link and no trailing space before the closing bracket. Keep seekable links only for supported web media. Cover local and web source behavior with generic fixtures.

## Notes

Reopened: Expanded print acceptance criteria: 8pt single-light-gray timestamps with no trailing gap, plus regression coverage for nested timestamp spans around frame captures.
