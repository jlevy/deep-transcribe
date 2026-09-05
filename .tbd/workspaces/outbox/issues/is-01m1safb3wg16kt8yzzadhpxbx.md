---
type: is
id: is-01m1safb3wg16kt8yzzadhpxbx
title: Left-align the claim chips within the claims outline
kind: task
status: closed
priority: 2
version: 2
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-05T17:39:46.427Z
updated_at: 2026-09-05T17:47:04.207Z
closed_at: 2026-09-05T17:47:04.206Z
close_reason: claim chips flush with the entry left edge (justify flex-start). Verified in the browser on the re-exported page; 1a9f95d.
resolution: null
duplicate_of: null
---
Owner: move the claim chips to be left-aligned within the claims outline (they are currently centered or otherwise not flush with the outline's left edge). Find the chip container styling in dt_viz.css.jinja / dt_concepts.js.jinja, left-align, verify in the browser on the Lex #501 export and in print.
