---
type: is
id: is-01kxj951e67pw82pex30hhhj74
title: Handle CLI keyboard interrupts without tracebacks
kind: bug
status: in_progress
priority: 2
version: 3
labels: []
dependencies: []
parent_id: is-01kxj4xxyfwmxmk3z9mebcf92x
created_at: 2026-07-15T06:59:11.941Z
updated_at: 2026-07-15T07:05:43.129Z
---
Catch KeyboardInterrupt at the Deep Transcribe process boundary, including interrupts during lazy imports, print a concise cancellation message, and return the conventional SIGINT exit code without a traceback. Compare kash handling and add a subprocess-level regression test.

## Notes

Root cause: the transcription-only try/except catches Exception, while KeyboardInterrupt derives from BaseException; lazy kash/transcription imports can therefore print a traceback. The fix wraps complete CLI dispatch at the process boundary, returns conventional exit code 130, and keeps native print handling independent of the lazy runtime stack. Regression test sends SIGINT in a subprocess and checks stderr and exit status.
