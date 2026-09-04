---
type: is
id: is-01m1nyv8q14zgfe1wypmpf6443
title: Pass product and proper names to speech-to-text as key terms
kind: feature
status: open
priority: 2
version: 1
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T10:18:50.976Z
updated_at: 2026-09-04T10:18:50.976Z
---
The transcription renders the same proper noun several ways, and every stage downstream
inherits the variants.

MEASURED on Lex #501, which is largely about one Linux distribution: the concept map
carries "Omarchy / Omachi Linux distribution", "Omakub Linux distribution", "Omarchi's
differentiation-first design", and a theme named "Building the Omakase/Omachi Distro".
Some of that is real — Omakub and Omarchy are genuinely different projects by the same
author — but Omakase, Omachi and Omarchi are all one word the recording says dozens of
times.

The reduce pass cannot fix this and should not try: it has no way to know that two
spellings are one product rather than two, and guessing would merge things that are
actually distinct.

FIX AT THE SOURCE. Deepgram accepts key terms, and this pipeline already threads a
--key-term flag through to it. What is missing is using it: for a recording whose title
and description name a product, those names are exactly the key terms to pass.

Two ways to get there, and the first is probably enough:
  1. Derive candidate key terms from the source metadata already fetched — title,
     description, chapter names — and pass them to transcription. Cheap, no model call,
     and the metadata is right there.
  2. Let a prior pass propose them, which costs a call and is only worth it if the
     metadata turns out to be too thin.

Note the cost of getting this wrong is high in one direction: key terms change the
transcription cache identity, so adding them means paying for speech-to-text again.
Worth doing when the transcript is first made, not as an afterthought.
