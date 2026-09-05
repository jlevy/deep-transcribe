---
type: is
id: is-01m1s97ny06r6tfr1ftczgx11r
title: Render >= and similar symbols in titles with KaTeX in a sans, normal-weight face
kind: feature
status: open
priority: 2
version: 2
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-05T17:18:06.783Z
updated_at: 2026-09-05T17:19:04.553Z
---
Owner: the >= character in the title looks ugly and bold. Render such symbols (>=, <=, ->, !=, x, etc.) via KaTeX (or a lightweight equivalent) but with the font adapted to match the surrounding sans type and weight rather than KaTeX's default serif math italic. Find where the glyph appears (title / headings / concept labels), decide whether to typeset only headings or all prose, and verify in the browser and in print.

## Notes

The Lex #501 export contains no >= or ≥ glyph outside minified JS. The owner's 'title of the explainer' must be another document (a docs page, a PDF, or a heading in a different export) — ask which before implementing. Candidate scope: headings and concept labels rendered through the page template.
