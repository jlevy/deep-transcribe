---
type: is
id: is-01m1s97njysjqc0w3rrt67cp2x
title: "Print layout: text column too wide, margins too small"
kind: bug
status: closed
priority: 2
version: 3
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-05T17:18:06.428Z
updated_at: 2026-09-05T18:27:33.758Z
closed_at: 2026-09-05T18:27:33.757Z
close_reason: "Withdrawn by the owner on 2026-09-05: the print-margins finding was a mistake. Measured identical to the SNL reference PDF."
resolution: null
duplicate_of: null
---
Owner, on the printed page: the text width should be narrower; the left and right margins are too small. Compare with docs/examples/snl-hotel-check-in-transcript.pdf (the intended print look). Adjust the @media print rules in dt_viz.css.jinja (and @page margins if set) so the column is narrower with generous margins; verify by printing the Lex #501 export to PDF from the browser at Letter and A4.

## Notes

Measured 2026-09-05 with Chrome headless print of the corrected Lex #501 export (279 pages) vs docs/examples/snl-hotel-check-in-transcript.pdf: identical text extents on every page checked (x 68..544 pt = 0.95 in margins each side, 6.60 in text). Page 1 renders like the reference. So the owner's 'explainer' with too-small margins is another document; waiting on which one before changing the print rules.
