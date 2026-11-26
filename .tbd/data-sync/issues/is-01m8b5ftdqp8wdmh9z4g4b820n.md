---
type: is
id: is-01m8b5ftdqp8wdmh9z4g4b820n
title: Support or clearly document WAV input for local transcription
kind: bug
status: open
priority: 3
version: 1
labels: []
dependencies: []
created_at: 2026-11-26T05:33:09.935Z
updated_at: 2026-11-26T05:33:09.935Z
---
Released v0.2.0 smoke testing found that the Kash local media format registry rejects a valid PCM WAV file as an unrecognized media URL. The same generated speech converted to MP3 transcribes successfully. Confirm the supported format contract and address WAV in the local media layer or document the accepted formats.
