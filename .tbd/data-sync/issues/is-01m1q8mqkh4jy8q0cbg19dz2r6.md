---
type: is
id: is-01m1q8mqkh4jy8q0cbg19dz2r6
title: Verify the current code on the full recording in a browser
kind: task
status: closed
priority: 0
version: 3
spec_path: docs/project/specs/active/plan-2026-09-04-long-form-stabilization.md
labels: []
dependencies: []
parent_id: is-01m1n945s0m25334ssbw9gfwqe
created_at: 2026-09-04T22:29:17.040Z
updated_at: 2026-09-05T00:05:00.042Z
closed_at: 2026-09-05T00:02:06.742Z
close_reason: "Verified in a browser on the 16:58 export of the current code: 11 timeline rows, 173 frames / 0 broken, 13 themes all collapsed (124 concepts), 13 per-theme graphs with 0 chips at x=0, 27 outline groups (largest 22, none under 3), Concepts panel 865 px, 0 warnings in the run. Per-stage: speaker 32, paragraphs 11, sections 32, outline 5, frames 3, concepts 8 min; 96 min total with transcription cached. Same-hints rerun: 13 s. Two defects filed from the evidence: dt-4hwa (collapse fragmentation) and dt-k1cf (thinning undershoot)."
resolution: null
duplicate_of: null
---
Phase 1 of the stabilization plan. None of today's fixes — hint exclusion actually wired into the analysis, the frame floor, the reduce carrying instructions, outward span rounding — has run on Lex #501. Run plain then --segments (script: /Volumes/spud-ext1/tmp/dt-scratch/fullscale.sh, workspace dt-final), then verify in a browser: frame count near 240 not 502, roughly a dozen themes, outline grouped, teaser collapsed with its heading intact, no broken frames, no traceback. Record per-stage minutes against the baseline in the spec (transcribe 12, speaker 31, paragraphs 12, sections 34, outline 5, frames 5, concepts 11). Close dt-hesk on the same evidence if the collapse renders as described.

## Notes

R1 evidence at scale: concept map 681 mentions, 0 inside the teaser window [5,109] s; outline 185 chips, 1 inside (the 4.56 s paragraph the pre-R7 span misses). 124 concepts, 13 themes, 0 unthemed.
