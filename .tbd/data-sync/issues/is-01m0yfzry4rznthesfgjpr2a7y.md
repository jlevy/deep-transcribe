---
type: is
id: is-01m0yfzry4rznthesfgjpr2a7y
title: Make the zero-install skill runner honor the yt-dlp freshness exception
kind: bug
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-08-26-self-documenting-skill.md
delegate: codex@spud10.local
labels:
  - packaging
dependencies: []
parent_id: is-01m0yf48parshvzra5k25xv9wr
hold: null
hold_until: null
created_at: 2026-08-26T07:36:38.069Z
updated_at: 2026-08-26T07:38:03.036Z
started_at: 2026-08-26T07:36:43.352Z
closed_at: 2026-08-26T07:38:03.036Z
close_reason: Rendered the reviewed yt-dlp cutoff into every version-pinned uvx runner, synchronized it with pyproject by test, updated release maintenance docs, and passed a clean built-wheel docs/skill/install smoke test under the global uv cool-off.
resolution: null
duplicate_of: null
---
The built wheel cannot resolve under the user's global 14-day uv cool-off because the package requires yt-dlp>=2026.8.19 but the CLI fallback does not carry the repository's reviewed per-package cutoff. Render the exact yt-dlp cutoff into zero-install commands, keep it synchronized with pyproject policy, and cover it with artifact smoke tests.
