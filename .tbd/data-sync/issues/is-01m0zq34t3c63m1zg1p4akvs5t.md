---
type: is
id: is-01m0zq34t3c63m1zg1p4akvs5t
title: Layer raw and rendered transcription caches
kind: feature
status: open
priority: 1
version: 1
labels: []
dependencies: []
parent_id: is-01m0zpq37wdhx51829qx0xmf0t
created_at: 2026-08-26T19:00:03.010Z
updated_at: 2026-08-26T19:00:03.010Z
---
Persist the paid provider response as a durable raw cache layer and derive versioned transcript HTML/text from it, so formatting, timestamp markup, and speaker-turn rendering can be regenerated without another speech-to-text request. Plan migration and cache-key semantics separately from the immediate cached-transcript normalization fix.
