---
type: is
id: is-01m10rzs362ec4pqvqffqw118r
title: Update every help, documentation, and skill surface
kind: task
status: closed
priority: 1
version: 4
spec_path: docs/project/specs/active/plan-2026-08-26-snl-example-single-command-cli.md
labels: []
dependencies:
  - type: blocks
    target: is-01kxj4zkw8vp8g4ebs496hwdgw
parent_id: is-01m10ryb6ze39bmjjq0chrxpbx
created_at: 2026-08-27T04:52:24.293Z
updated_at: 2026-08-27T05:08:16.502Z
closed_at: 2026-08-27T05:08:16.501Z
close_reason: Committed in 9c32b6f. README, packaged guide, canonical skill, generated mirrors, installation guide, and E2E runbook now teach one direct-source CLI and --models; a drift test rejects the legacy forms. Lint/type checks, 66 tests, and builds pass.
resolution: null
duplicate_of: null
---
Rewrite the CLI epilog, README commands, packaged guide, canonical skill, generated skill mirrors, installation/context docs, and E2E runbook for the hard-cut direct-source contract. Add a drift check that no authored surface teaches legacy subcommands.

## Notes

Updating every authored help/documentation surface to the direct-source CLI, then regenerating skill mirrors and adding a legacy-syntax drift assertion.
