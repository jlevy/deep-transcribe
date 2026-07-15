---
type: is
id: is-01kxhe5pq7df6tyah55ydk77ay
title: "Upgrade transitive model defaults for deep-transcribe PR #2"
kind: task
status: closed
priority: 1
version: 6
labels: []
dependencies: []
parent_id: is-01kxj4xxyfwmxmk3z9mebcf92x
created_at: 2026-07-14T23:07:42.181Z
updated_at: 2026-07-15T05:46:07.008Z
closed_at: 2026-07-15T00:42:42.954Z
close_reason: Published the patch dependency chain and passed the full Deep Transcribe release E2E gate with both providers.
---

## Notes

Completed the current model-stack upgrade across the full dependency tree.

- Merged and published kash-shell 0.4.3 (kash#12 and corrective Python 3.14 packaging PR kash#13).
- Merged and published kash-docs 0.2.1 (kash-docs#2).
- Merged and published kash-media 0.4.1 (kash-media#3).
- Deep Transcribe PR #2 is current with main, CI-green, and ready for review at commit 4d12141.
- Deepgram live request passed with Nova-3 and diarize_model=latest.
- Anthropic and OpenAI annotated profiles passed using all six configured fast, standard/structured, and careful models.
- Manual/model review passed: 550 words, 29 correctly labeled speaker paragraphs, 29 monotonic timestamps, accurate annotations, and 19 valid frame captures in each provider export.
- Added and exercised tests/e2e-test.runbook.md; fixed final HTML frame-asset copying and added regression coverage.
- No stale model references remain in active code or documentation.
