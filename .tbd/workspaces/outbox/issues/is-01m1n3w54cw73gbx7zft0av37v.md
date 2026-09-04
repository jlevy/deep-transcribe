---
type: is
id: is-01m1n3w54cw73gbx7zft0av37v
title: Make the views respect exclusions
kind: task
status: open
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-09-04-long-form-stabilization.md
labels: []
dependencies: []
parent_id: is-01m1n3q978x6fyhsyfm175ngy6
created_at: 2026-09-04T02:27:28.515Z
updated_at: 2026-09-04T22:29:18.158Z
---
Excluded units are marked in the index, never deleted, and every surface agrees. Transcript: an excluded run collapses to one line with a kind chip (INTRO/SPONSOR/OUTRO/DUPLICATE), duration, and time, reusing the concept chip vocabulary; clicking expands the passage in place in the supporting gray, so a reader can drill in but is not made to scroll through six minutes of ads. Analysis: synopsis, outline, concepts, and claims read only included units. Statistics: speaker figures are content-only with excluded time reported separately. Timeline: excluded spans shaded distinctly so their share stays visible. Print: the collapsed line only, not the full passage.

## Notes

Substantially done as of today. Transcript: collapseSegments in dt_core.js.jinja folds a suppressed run to one line with the purpose name, duration and 'left out of the analysis', click to expand; R4 fixed the heading being stolen from a partly-suppressed section. Analysis: hints now reach the outline, synopsis and concept extractor (R1, e1469ee) — before today they did not. Difference from the description: the chip reads the purpose name (Teaser/Ad/...) rather than INTRO/SPONSOR/OUTRO/DUPLICATE. Close after the full-scale browser check (see the verify bead under dt-qc7j).
