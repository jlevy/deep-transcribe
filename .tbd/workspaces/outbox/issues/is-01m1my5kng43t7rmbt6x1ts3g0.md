---
type: is
id: is-01m1my5kng43t7rmbt6x1ts3g0
title: Declare and enforce the dt text-color roles
kind: task
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-31-transcript-timeline-and-concept-map.md
labels: []
dependencies: []
created_at: 2026-09-04T00:47:46.863Z
updated_at: 2026-09-04T00:49:55.225Z
closed_at: 2026-09-04T00:49:55.225Z
close_reason: "Verified on the SNL test bed: tracks aligned with the Timeline scale, mention tooltips show transcript excerpts, headings uniformly black, single chip rendering"
resolution: null
duplicate_of: null
---
Three documented text roles, declared once as tokens and used everywhere in the dt UI: --dt-text (content, near-black), --dt-text-support (one mid gray for supporting labels), --dt-text-faint (light gray, timestamps only). Panel titles explicitly take --dt-text so headings never inherit context grays (the Summary title was inheriting the description's gray). Accent colors come only from the speaker and kind variables.
