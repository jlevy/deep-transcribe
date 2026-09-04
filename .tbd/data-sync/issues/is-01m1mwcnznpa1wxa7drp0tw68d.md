---
type: is
id: is-01m1mwcnznpa1wxa7drp0tw68d
title: Darken tooltip hover targets with a fast transition
kind: task
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-31-transcript-timeline-and-concept-map.md
labels: []
dependencies: []
created_at: 2026-09-04T00:16:41.447Z
updated_at: 2026-09-04T00:20:04.818Z
closed_at: 2026-09-04T00:20:04.817Z
close_reason: Implemented and verified on the SNL test bed; timeline type at design-system sizes confirmed by capture
resolution: null
duplicate_of: null
---
Every element the tooltip component attaches to gets a shared hover treatment: a slight darken (brightness filter) with a fast, clean CSS transition, applied automatically by tooltip.attach so all tooltip targets behave identically. Reduced motion disables the transition.
