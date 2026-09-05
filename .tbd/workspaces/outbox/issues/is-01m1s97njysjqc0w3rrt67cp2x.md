---
type: is
id: is-01m1s97njysjqc0w3rrt67cp2x
title: "Print layout: text column too wide, margins too small"
kind: bug
status: open
priority: 2
version: 1
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-05T17:18:06.428Z
updated_at: 2026-09-05T17:18:06.428Z
---
Owner, on the printed page: the text width should be narrower; the left and right margins are too small. Compare with docs/examples/snl-hotel-check-in-transcript.pdf (the intended print look). Adjust the @media print rules in dt_viz.css.jinja (and @page margins if set) so the column is narrower with generous margins; verify by printing the Lex #501 export to PDF from the browser at Letter and A4.
