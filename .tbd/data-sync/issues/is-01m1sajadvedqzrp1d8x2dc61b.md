---
type: is
id: is-01m1sajadvedqzrp1d8x2dc61b
title: Speaker label unstyled on a turn the heading stage split
kind: bug
status: closed
priority: 1
version: 2
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-05T17:41:24.027Z
updated_at: 2026-09-05T17:47:04.799Z
closed_at: 2026-09-05T17:47:04.798Z
close_reason: second decoration pass; 885 styled labels, 0 bare; the split-off DHH paragraph now styled. Verified in the browser on the re-exported page; 1a9f95d.
resolution: null
duplicate_of: null
---
Owner, on the Lex #501 page under 'From Pre-Agentic to Agentic Era': 'DHH: To me, that's why…' renders as plain bold, not the styled speaker label. The markdown is right (**DHH:**) but the paragraph lacks the speaker-label span every other turn carries: kash's insert_section_headings split a long turn at the heading and rewrote the continuation's label as bare markdown. Fix: after section headings, a deterministic pass that finds paragraphs beginning with **Name:** for a roster name and no preceding span, and wraps the label in the same span (speaker id from the roster map). Count and verify on the real item; check whether v1 had it too.
