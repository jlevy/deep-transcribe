---
type: is
id: is-01m1qfsw4s805mrwj6m6ckghkb
title: Re-export without rerunning any stage
kind: feature
status: open
priority: 2
version: 1
spec_path: docs/project/specs/active/plan-2026-09-04-long-form-stabilization.md
labels: []
dependencies: []
parent_id: is-01m1qfkw8vxpzmyds5qsxm798b
created_at: 2026-09-05T00:34:25.560Z
updated_at: 2026-09-05T00:34:25.560Z
---
During the quality loop I rebuilt the page several times without changing any analysis (after JS template fixes, after --elements changes) and had to do it through a Python script calling format_results, or by rerunning the CLI and relying on every stage being cached (13 s, but noisy). Add --export-only (or make --elements changes never invalidate stages) so an agent can regenerate the HTML from the cached final item in one obvious command. Print the export path.
