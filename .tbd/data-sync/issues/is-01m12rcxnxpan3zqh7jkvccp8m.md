---
type: is
id: is-01m12rcxnxpan3zqh7jkvccp8m
title: Re-check the Deepgram rationale against providers that now diarize
kind: task
status: open
priority: 2
version: 1
labels: []
dependencies: []
parent_id: is-01m0zpq37wdhx51829qx0xmf0t
created_at: 2026-08-27T23:20:35.261Z
updated_at: 2026-08-27T23:20:35.261Z
---
The intended README rationale is that Deep Transcribe uses Deepgram because competing speech APIs, notably Whisper, do not do speaker diarization. That premise no longer holds as stated.

Checked https://developers.openai.com/api/docs/guides/speech-to-text: OpenAI now lists gpt-4o-transcribe-diarize alongside gpt-transcribe, gpt-4o-transcribe, gpt-4o-mini-transcribe, and legacy whisper-1. The docs say to use gpt-4o-transcribe-diarize 'only when you need to identify who speaks during different parts of a recording', and the diarized_json response format returns 'segments with speaker, start, and end metadata'. It is file-transcription only, not realtime.

So: whisper-1 alone still does not diarize, but 'the standard APIs do not diarize' is no longer accurate about OpenAI's lineup.

Follow-up: check AssemblyAI, Speechmatics, and Google STT diarization parity, then decide whether the README makes a comparative claim at all or just states the requirement (the pipeline needs speaker-attributed transcripts) and names the backend. Any comparative claim needs a dated citation, per the calibrate-confidence guideline.

Also worth measuring rather than asserting: run the SNL example through a diarizing alternative and compare speaker boundaries against the Deepgram result.
