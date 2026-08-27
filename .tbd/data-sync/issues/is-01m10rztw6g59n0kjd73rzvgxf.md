---
type: is
id: is-01m10rztw6g59n0kjd73rzvgxf
title: Validate the hard cut and prepare the pull request
kind: task
status: closed
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-08-26-snl-example-single-command-cli.md
labels: []
dependencies:
  - type: blocks
    target: is-01m110ce5yx0f76cycakj7qjaq
parent_id: is-01m10ryb6ze39bmjjq0chrxpbx
created_at: 2026-08-27T04:52:26.117Z
updated_at: 2026-08-27T07:01:55.917Z
closed_at: 2026-08-27T07:01:55.915Z
close_reason: "Branch passed full local gates and GitHub Actions, PR #14 has a detailed validation plan and is clean to merge."
resolution: null
duplicate_of: null
---
Run lint, type checks, tests, builds, generated-skill drift validation, installed-package smoke tests, and the public E2E runbook. Commit coherent changes, push the branch, open the pull request, and verify CI.

## Notes

Full local lint, type, 75-test pytest suite, three Tryscript goldens, lock check, and wheel/sdist build pass. Branch is committed; next push, PR validation plan, CI, merge, release, and installed-artifact smoke.
