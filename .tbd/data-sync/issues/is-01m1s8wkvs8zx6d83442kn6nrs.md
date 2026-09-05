---
type: is
id: is-01m1s8wkvs8zx6d83442kn6nrs
title: Page layout lost the left contents column and the right gutter
kind: bug
status: open
priority: 1
version: 2
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-05T17:12:04.216Z
updated_at: 2026-09-05T17:14:28.874Z
---
Regression reported by the owner on the final Lex #501 export: the main text column moved horizontally. The intended layout is the table of contents on the left, the text in the middle, and a free right-hand gutter that the vertical timeline slides into on scroll and that the frame captures render in. Now the rail overlaps the text at the right edge and there is no gutter. Find the commit on claude/standalone-package-longform that changed the page grid in dt_viz.css.jinja (origin/main is the reference layout), restore the three-column arrangement while keeping the new components' styles, and verify in the browser at 1280x900 and at a wide window.

## Notes

CAUSE: this branch bumped kash-shell 0.4.10 -> 0.4.11 (and kash-media 0.4.8 -> 0.4.9). The page grid .content-with-toc.has-toc comes from kash's toc_styles/base_styles, not from dt_viz.css (no layout rule differs from origin/main). Measured at 1280 px: grid 333px + 995px, text to x=1269, rail at x=1200 over the text, frames absolutely positioned into a gutter at x=1423 (off-screen). dt-sy01 (labels) and dt-fs0g (rail) are downstream of this.
