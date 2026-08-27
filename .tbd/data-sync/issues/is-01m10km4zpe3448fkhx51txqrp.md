---
type: is
id: is-01m10km4zpe3448fkhx51txqrp
title: Create and visually validate the hotel sample PDF
kind: task
status: closed
priority: 1
version: 8
labels: []
dependencies: []
parent_id: is-01m10kjrzedwht5b4mqbmwm3yp
created_at: 2026-08-27T03:18:40.373Z
updated_at: 2026-08-27T04:27:15.848Z
closed_at: 2026-08-27T04:27:15.848Z
close_reason: "Implemented and committed in 3845021; PR #13 is open and all CI checks pass."
resolution: null
duplicate_of: null
---
Print the public hotel HTML with a real browser, render representative pages, inspect typography and links, and keep the resulting PDF untracked until approved.

## Notes

The user approved the final sample. The Chrome/Skia PDF and preview are committed in 3845021: seven tagged Letter pages, 29 timestamp links, a 9pt light-gray timestamp/footer treatment, no clipped frame turns, and visual inspection of every page. PR #13 CI passes.
