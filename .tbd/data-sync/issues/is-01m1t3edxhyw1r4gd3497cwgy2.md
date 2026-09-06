---
type: is
id: is-01m1t3edxhyw1r4gd3497cwgy2
title: Roster inference finds nothing from context that names no roles; the two-ID fallback merges five voices into one paragraph
kind: bug
status: open
priority: 3
version: 1
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-06T00:56:10.928Z
updated_at: 2026-09-06T00:56:10.928Z
---
SNL from scratch with --context 'a hotel clerk and two guests' (no names): infer_speaker_roster_from_context yields no roster, kash identify_speakers maps Deepgram's two IDs to 'Hotel Clerk' and 'Guest', and the whole check-in scene lands in one 300-word paragraph labeled Guest. With the documented five-role context the same run gives five labels, 45 paragraphs, 104 corrected utterances. Not a regression (the fallback is kash's), but the report should say the roster was not inferred, and the source description (which names the performers) could feed the inference.
