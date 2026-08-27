---
type: is
id: is-01m10tcjrjp61h2qdkn0vqpnp2
title: Add Tryscript golden coverage for the unified CLI
kind: task
status: closed
priority: 1
version: 2
spec_path: docs/project/specs/active/plan-2026-08-26-snl-example-single-command-cli.md
labels: []
dependencies: []
parent_id: is-01m10ryb6ze39bmjjq0chrxpbx
created_at: 2026-08-27T05:16:52.368Z
updated_at: 2026-08-27T05:24:02.025Z
closed_at: 2026-08-27T05:24:02.025Z
close_reason: Implemented bounded delimiter-safe source evidence, prose-to-roster inference with explicit override precedence, and a deterministic Tryscript golden for the unified CLI; full lint, type, Python, and golden tests pass.
resolution: null
duplicate_of: null
---
Add a small, language-neutral Tryscript golden that executes the installed development CLI and captures the complete stable help, model-listing, and representative parser-error surfaces. Wire it into the normal test workflow without network or API calls, document how to update it, and retain focused Python tests only where they add independent evidence.
