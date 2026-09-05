---
type: is
id: is-01m1s8pn6129vv1bcp0b32vzew
title: Horizontal timeline block labels truncated to one short line again
kind: bug
status: closed
priority: 1
version: 2
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-05T17:08:48.948Z
updated_at: 2026-09-05T17:27:32.035Z
closed_at: 2026-09-05T17:27:32.034Z
close_reason: "Cause: the 5.8px/char estimate ran ~15% narrow for the label face, so long labels stayed single-line and spilled into the next block (158px in 118px). ead0e59 measures text with a scratch element sharing the label class. After: 23 labels, none overflowing, two wrapped to two lines."
resolution: null
duplicate_of: null
---
Regression reported by the owner on the final Lex #501 export: the named section blocks in the horizontal timeline used to carry two lines of wrapped text and were legible; now each block shows a short, heavily truncated label that is barely readable. Find the commit on claude/standalone-package-longform that changed the label layout in dt_timeline.js.jinja / dt_viz.css.jinja (or whether the 23-chapter sections changed the block geometry), restore the two-line wrapped labels, and verify in the browser at 1280x900 on the final export.
