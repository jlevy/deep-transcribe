---
type: is
id: is-01m1rg10ga7gzk0hcsax2vv1e1
title: "Add a rerun-from STAGE flag: recompute one stage and everything below it"
kind: feature
status: open
priority: 2
version: 1
spec_path: docs/project/specs/active/plan-2026-09-04-agent-iteration-loop.md
labels: []
dependencies: []
parent_id: is-01m1qfkw8vxpzmyds5qsxm798b
created_at: 2026-09-05T09:57:33.833Z
updated_at: 2026-09-05T09:57:33.833Z
---
kash caches a stage output on its input item, not on the stage code, so after fixing demote_model_headings the recipe rerun completed in 45 s with 0 LLM calls and the export still had the bug. The only documented remedy is --rerun-processing (about 96 min at five hours). Done by hand instead: read each doc item source.operation.action_name, move the items from the fixed stage onward (plus .doc.assets) to a backup dir, rerun; recomputed in about 25 min. Make that a flag, --rerun-from STAGE: set aside (never delete) the current lineage items from that stage onward and rerun; list stage names in --help; refuse an unknown stage. Rerun-table row: a stage code changed, use --rerun-from STAGE. Test through the CLI with a fake pipeline, asserting exactly the downstream stages re-run and the upstream ones do not.
