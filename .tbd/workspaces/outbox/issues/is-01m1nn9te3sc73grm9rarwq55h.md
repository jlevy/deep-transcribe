---
type: is
id: is-01m1nn9te3sc73grm9rarwq55h
title: Make the concept graph legible at a hundred concepts
kind: task
status: in_progress
priority: 1
version: 2
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T07:32:02.113Z
updated_at: 2026-09-04T08:35:00.557Z
---
With the definition list grouped into themes, the concept graph is what keeps the
Concepts panel long.

MEASURED on the 5.3-hour run (115 concepts, 12 themes, at 1200 px):
  definition list      729 px   (12 collapsed theme lines)
  Concepts panel     4,408 px   (so ~3,700 px of it is the graph)
  graph elements       455

The graph is a time-layered chip layout: chips are packed into rows by first-mention
time, so 115 chips means many rows of chips and a tall block. It was designed for a
couple of dozen concepts, and at that size it is genuinely useful.

Options, roughly in order of appeal:
  1. Draw the graph per theme, next to (or inside) the theme group, so it is 12 small
     graphs of ~9 chips rather than one of 115. Relations that cross themes would need
     handling — either drawn between groups or listed rather than drawn.
  2. Graph only the concepts that carry relations, since a chip with no edges adds
     height and says nothing the definition list does not.
  3. Keep one graph but show only the top concepts by mention count, with the rest
     reachable through the themed list.

Whatever the choice, short media must be unchanged: the graph at 24 concepts is fine and
the SNL example must render identically.

## Notes

IMPLEMENTED in 1e3b235, not yet seen rendered.

When there are themes and more than 30 concepts, each theme group gets its own graph of
its own concepts and the single graph of everything is not drawn. Expected on the
5.3-hour run: 12 graphs of about 9 chips, against one of 115.

Key implementation note, because it is the bug this design invites: the layout depends on
measured chip widths and a hidden element measures as zero, so the groups are built
EXPANDED, the graphs are laid out, and only then are the groups collapsed. Get that order
wrong and every chip stacks at x=0 inside the collapsed group. Each graph is built inside
a guard so a graph that will not lay out is dropped rather than taking the list with it.

TRADE-OFF ACCEPTED: relations crossing themes are no longer drawn as edges. They are not
lost — buildDefinitions already renders every relation as a print-only line under its
concept — but the drawing is within-theme only. If cross-theme relations turn out to
matter visually, the options are drawing them between groups or listing them on the
theme head.

NOT YET VERIFIED IN A BROWSER. Check on the clean run's export:
  - 12 graphs, one per theme, each with its theme's chips and no chip at x=0
  - the Concepts panel height, which was 4,408 px with a 729 px list and ~3,700 px graph
  - print still shows the full-width graph from the print host
  - selecting a chip still dims across the panel and the Claims panel
