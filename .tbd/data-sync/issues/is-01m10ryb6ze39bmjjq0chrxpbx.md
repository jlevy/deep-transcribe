---
type: is
id: is-01m10ryb6ze39bmjjq0chrxpbx
title: Unify CLI and publish the SNL Hotel Check-In example
kind: epic
status: open
priority: 1
version: 24
spec_path: docs/project/specs/active/plan-2026-08-26-snl-example-single-command-cli.md
labels: []
dependencies: []
child_order_hints:
  - is-01m10rzra03r520c3m5atxs9rr
  - is-01m10rzrnq9wrzrpwfahq6xz2m
  - is-01m10rzsfvq0ramn2v7xez900n
  - is-01m10s3fq85s3f5hrb4ea83n1p
  - is-01m10rzs362ec4pqvqffqw118r
  - is-01m10rzsv6hrkq26y5kf7r7a8q
  - is-01kxj4zkw8vp8g4ebs496hwdgw
  - is-01m10rztw6g59n0kjd73rzvgxf
  - is-01m10tcjrjp61h2qdkn0vqpnp2
  - is-01m10v3kvfn09bvkxf65kzmzj8
  - is-01m10vy9q46584rk97aa5s8fdb
  - is-01m10vzjncar8rvyy09zn10n69
  - is-01m10wh80jfcybq1jsn699kqqv
  - is-01m10wjnjn89mhyndnkk1d48an
  - is-01m10wnk8b69y5h4vpvydj5mrc
  - is-01m10wnrd9qzrjzp4660pagqbw
  - is-01m10wnxavh33kzbzms1qne5bb
  - is-01m10wvqgjer8jbhx22ncvbc8r
  - is-01m110ce5yx0f76cycakj7qjaq
created_at: 2026-08-27T04:51:37.310Z
updated_at: 2026-08-27T07:01:39.133Z
---
Implement the linked plan as a hard-cut pre-alpha change: one direct-source CLI and help surface, an optional-value --models flag, bounded YouTube metadata in semantic context, and a reviewed public SNL Hotel Check-In transcript showcase.

## Notes

Unified CLI, source-aware context, prose roster inference, Tryscript goldens, stage-specific overview prompts, and cache-boundary fixes are implemented locally. The public SNL run is content-reviewed and proves instruction-only cache reuse. Pre-commit review found and fixed source-metadata restoration and moved generic SkipItem lineage handling upstream to Kash. Next: commit, PR, CI, and patch releases in dependency order; then generate and visually approve the public PDF/preview.
