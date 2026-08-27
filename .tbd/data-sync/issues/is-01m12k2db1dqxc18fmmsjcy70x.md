---
type: is
id: is-01m12k2db1dqxc18fmmsjcy70x
title: Raise the kash-media floor and release deep-transcribe v0.1.14
kind: task
status: open
priority: 1
version: 2
labels: []
dependencies: []
parent_id: is-01m1118hwdhra16fmaz6jd1smt
created_at: 2026-08-27T21:47:27.968Z
updated_at: 2026-08-27T23:51:45.725Z
---
After kash-media 0.4.8 publishes:

1. uv add --exclude-newer "14 days" "kash-media>=0.4.8,<0.5"
2. uv lock, make lint && make test
3. Tag v0.1.14

jlevy/deep-transcribe#16 can merge before this — it reads every field through .get() with isinstance guards, so it degrades safely on the current releases. This bump is what guarantees the discovery fields are actually present.

Optional cleanup: deep-transcribe imports kash.exec and kash.model directly but declares no kash-shell dependency, the same gap that was just fixed in kash-media.

Current: deep-transcribe v0.1.13.

## Notes

Release-ordering trap found in review (2026-08-27). The skill's version pin and the youtube extra must move together.

skill_support.DISCOVERY_VERSION is still "0.1.13", so a source checkout renders:

  --from "deep-transcribe[youtube]==0.1.13"

0.1.13 has no youtube extra, and uv silently ignores an unknown extra rather than failing (verified: uvx --from "cowsay[nope]==6.1" runs fine). So the pin resolves without Deno and degrades quietly, which is exactly the failure the extra was added to remove.

Add to the release steps, after tagging v0.1.14:
1. Set DISCOVERY_VERSION = "0.1.14" in src/deep_transcribe/skill_support.py
2. Re-run the skill sync so all three mirrors carry the new pin
3. Confirm the rendered runner reads deep-transcribe[youtube]==0.1.14

v0.1.14 now also ships the youtube extra, not just the kash-media floor bump.
