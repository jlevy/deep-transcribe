---
type: is
id: is-01m1s8pnh7wvc7vzs8r4n5285w
title: Vertical timeline shows before the reader scrolls to the transcript
kind: bug
status: open
priority: 1
version: 2
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-05T17:08:49.319Z
updated_at: 2026-09-05T17:18:06.298Z
---
Regression reported by the owner: the vertical timeline used to appear only once the reader scrolled down to the transcript; on the final Lex #501 export it is visible from the start. Find the commit that removed or broke the scroll gating (IntersectionObserver / scroll handler in dt_core.js.jinja or dt_timeline.js.jinja), restore it, and verify in the browser: hidden at load, visible after scrolling into the transcript.

## Notes

CAUSE: dt_rail.js updateVisibility uses the first transcript unit's rect; with the teaser collapsed at the top (display:none) that rect is 0,0 so 'top < 75% of viewport' is true at load. Regression from the segment collapse. Fix: first RENDERED unit (getClientRects().length > 0).
