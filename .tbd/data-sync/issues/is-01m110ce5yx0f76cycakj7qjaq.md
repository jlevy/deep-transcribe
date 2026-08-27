---
type: is
id: is-01m110ce5yx0f76cycakj7qjaq
title: Release Deep Transcribe 0.1.13 and smoke-test the installed package
kind: task
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-26-snl-example-single-command-cli.md
labels: []
dependencies: []
parent_id: is-01m10ryb6ze39bmjjq0chrxpbx
created_at: 2026-08-27T07:01:39.133Z
updated_at: 2026-08-27T07:10:23.238Z
closed_at: 2026-08-27T07:10:23.237Z
close_reason: "Released v0.1.13 from merged PR #14; trusted publish and PyPI propagation passed, and the exact installed artifact passed version, help, models, docs, skill installation, and public cache-aware rerun smokes."
resolution: null
duplicate_of: null
---
Merge the green Deep Transcribe PR, create the v0.1.13 tag and GitHub release, verify the trusted publishing workflow and PyPI artifact, then exercise help, models, docs, skill installation, and the public cache-aware example from the installed package.

## Notes

PR #14 is green and clean to merge. Next: merge, tag v0.1.13, verify trusted publish, and smoke-test the installed artifact.
