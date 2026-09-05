---
type: is
id: is-01m1sakf28njeegwcwzkd5e184
title: Speaker names in faux small caps, consistently
kind: task
status: open
priority: 2
version: 1
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-05T17:42:01.542Z
updated_at: 2026-09-05T17:42:01.542Z
---
Owner: render names like 'Lex Fridman' in small caps everywhere they appear as labels (transcript turn labels, folded asides, rail/timeline tooltips, claim made-by chips, roster) — not with font-variant small-caps (font support varies) but with text-transform: uppercase at a reduced size and slight letter-spacing, in one shared CSS rule so it is consistent. Verify in the browser and in print.
