---
type: is
id: is-01m10ryb6ze39bmjjq0chrxpbx
title: Unify CLI and publish the SNL Hotel Check-In example
kind: epic
status: open
priority: 1
version: 12
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
created_at: 2026-08-27T04:51:37.310Z
updated_at: 2026-08-27T04:56:26.925Z
---
Implement the linked plan as a hard-cut pre-alpha change: one direct-source CLI and help surface, an optional-value --models flag, bounded YouTube metadata in semantic context, and a reviewed public SNL Hotel Check-In transcript showcase.

## Notes

Plan spec committed as c2c917c on codex/snl-hotel-single-command and pushed. The pre-commit review added dt-vot2 so ordinary prose can produce the internal five-speaker roster without structured CLI input. Full lint/type checks, 60 tests, and wheel/sdist builds passed. Next ready implementation bead: dt-ojgn.
