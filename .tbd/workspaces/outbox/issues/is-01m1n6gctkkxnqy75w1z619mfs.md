---
type: is
id: is-01m1n6gctkkxnqy75w1z619mfs
title: "Track upstream kash PR #23 through release"
kind: task
status: closed
priority: 1
version: 4
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T03:13:28.914Z
updated_at: 2026-09-04T08:16:45.920Z
closed_at: 2026-09-04T08:16:45.920Z
close_reason: "Full sequence done: kash #23 merged and released as v0.4.11 to PyPI, kash-media #12 merged and released as v0.4.9, deep-transcribe pins bumped and the editable overlays dropped. 127 tests pass against the published wheels."
resolution: null
duplicate_of: null
---
Two upstream PRs, both CI-green, consumed locally via editable overlays:
  kash PR #23 — TranscriptionLimits (long-audio request budget)
  kash-media PR #12 — VideoDownloadOptions, remux instead of re-encode

Release sequence once the long-form run validates end to end:
  1. merge kash #23, cut a kash release
  2. merge kash-media #12, bump its kash-shell pin, cut a kash-media release
  3. bump deep-transcribe's kash-shell and kash-media pins
  4. drop the local editable overlays (uv pip install -e ../kash, ../kash-media --no-deps)

Note: both local checkouts were moved from v0.3.37/v0.3.19 to current main to do this work, so their git state differs from how they were found.

## Notes

RELEASE SEQUENCE EXECUTED 2026-09-04, on the user's explicit go-ahead to merge and cut
releases.

  kash #23        merged as e38c25f, tagged v0.4.11, GitHub release published,
                  PyPI publish dispatched on the tag
  kash-media #12  merged as 6d43acc, tagged v0.4.9, GitHub release published,
                  PyPI publish dispatched on the tag

Worth recording, because it will bite again: creating the GitHub Release from
github-release.yml does NOT trigger publish.yml. A workflow authenticated with
GITHUB_TOKEN cannot trigger further workflows, so the `release: published` event never
fires. Both publishes had to be dispatched by hand, and they must be dispatched with
`--ref <tag>` rather than on main, because versioning is dynamic from git tags and a
main-ref build would publish a dev version.

kash-media's own kash-shell pin was deliberately NOT bumped: it stays at >=0.4.10,<0.5
because kash-media does not reference TranscriptionLimits or anything else new in 0.4.11.
Bumping a pin for a dependency you do not use makes the constraint dishonest.

REMAINING: bump deep-transcribe's pins to kash-shell>=0.4.11 and kash-media>=0.4.9, then
drop the local editable overlays (uv pip install -e ../kash, ../kash-media --no-deps) and
confirm the test suite still passes against the published wheels rather than the local
checkouts.
