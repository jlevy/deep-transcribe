---
type: is
id: is-01m10pqak9vwp3nykvpwj6g1st
title: Increase printed timestamp and footer text size
kind: bug
status: closed
priority: 1
version: 4
labels: []
dependencies: []
parent_id: is-01m10kjrzedwht5b4mqbmwm3yp
created_at: 2026-08-27T04:12:50.144Z
updated_at: 2026-08-27T04:21:18.436Z
closed_at: 2026-08-27T04:21:18.435Z
close_reason: The 9pt treatment is legible without competing with the transcript; focused and full tests pass.
resolution: null
duplicate_of: null
---
Increase the hotel sample's printed timestamp and footer text slightly while preserving the shared light-gray treatment. Regenerate with Chrome, inspect all pages, and keep the PDF untracked until approved.

## Notes

Changed the printed timestamp and Deep Transcribe footer from 8pt to 9pt while preserving the same var(--color-tertiary) light gray. Regenerated the public sample from the saved final transcript item with Chrome/Skia and visually inspected all seven pages.
