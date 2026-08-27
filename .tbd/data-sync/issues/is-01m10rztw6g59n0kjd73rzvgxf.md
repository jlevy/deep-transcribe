---
type: is
id: is-01m10rztw6g59n0kjd73rzvgxf
title: Validate the hard cut and prepare the pull request
kind: task
status: in_progress
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-08-26-snl-example-single-command-cli.md
labels: []
dependencies: []
parent_id: is-01m10ryb6ze39bmjjq0chrxpbx
created_at: 2026-08-27T04:52:26.117Z
updated_at: 2026-08-27T06:59:06.559Z
---
Run lint, type checks, tests, builds, generated-skill drift validation, installed-package smoke tests, and the public E2E runbook. Commit coherent changes, push the branch, open the pull request, and verify CI.

## Notes

Full local lint, type, 75-test pytest suite, three Tryscript goldens, lock check, and wheel/sdist build pass. Branch is committed; next push, PR validation plan, CI, merge, release, and installed-artifact smoke.
