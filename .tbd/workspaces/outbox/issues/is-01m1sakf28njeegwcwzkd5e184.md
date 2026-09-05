---
type: is
id: is-01m1sakf28njeegwcwzkd5e184
title: Speaker names in faux small caps, consistently
kind: task
status: closed
priority: 2
version: 2
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-05T17:42:01.542Z
updated_at: 2026-09-05T17:47:05.085Z
closed_at: 2026-09-05T17:47:05.084Z
close_reason: uppercase transform at 0.82em with tracking on .dt-name, tooltips, stats, claim speakers, name refs. Verified in the browser on the re-exported page; 1a9f95d.
resolution: null
duplicate_of: null
---
Owner: render names like 'Lex Fridman' in small caps everywhere they appear as labels (transcript turn labels, folded asides, rail/timeline tooltips, claim made-by chips, roster) — not with font-variant small-caps (font support varies) but with text-transform: uppercase at a reduced size and slight letter-spacing, in one shared CSS rule so it is consistent. Verify in the browser and in print.
