---
type: is
id: is-01m1n24twy5fnkdf5hnpfqr4hh
title: Guard the CLI golden's version placeholder
kind: bug
status: open
priority: 1
version: 1
labels: []
dependencies: []
created_at: 2026-09-04T01:57:15.805Z
updated_at: 2026-09-04T01:57:15.805Z
---
tryscript run --update replaces [VERSION] with the local dev version, so CI fails on its own hash — this has now happened twice. Restore the placeholder and add a test that fails locally whenever a literal version is baked into the golden.
