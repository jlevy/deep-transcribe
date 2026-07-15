---
type: is
id: is-01kxj951e67pw82pex30hhhj74
title: Handle CLI keyboard interrupts without tracebacks
kind: bug
status: in_progress
priority: 2
version: 4
labels: []
dependencies: []
parent_id: is-01kxj4xxyfwmxmk3z9mebcf92x
created_at: 2026-07-15T06:59:11.941Z
updated_at: 2026-07-15T07:09:42.678Z
---
Catch KeyboardInterrupt at the Deep Transcribe process boundary, including interrupts during lazy imports, print a concise cancellation message, and return the conventional SIGINT exit code without a traceback. Compare kash handling and add a subprocess-level regression test.

## Notes

Merged as PR #7 and released as deep-transcribe 0.1.10 after PR and main CI passed. Published artifact smoke test and global reinstall remain; defer reinstall until the user current 0.1.9 transcription process exits so its environment is not replaced mid-run.
