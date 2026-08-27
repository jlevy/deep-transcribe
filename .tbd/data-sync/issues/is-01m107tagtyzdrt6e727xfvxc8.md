---
type: is
id: is-01m107tagtyzdrt6e727xfvxc8
title: Release the first-party transcription stack
kind: epic
status: closed
priority: 1
version: 12
labels: []
dependencies: []
parent_id: is-01m0zpq37wdhx51829qx0xmf0t
child_order_hints:
  - is-01m107q73p72w6xhebb6jr66tv
  - is-01m107q7cbhybbteyqfxg4esyq
  - is-01m107q7mqbhw6gb5cjqax4vhs
  - is-01m107q7x6bxhqwhqqgg10hx6j
  - is-01m107za1769d9gk5t29g48nyq
  - is-01m109e76rzkc4j2tqqf39r27h
  - is-01m109ec7nh773zjacw7szyvmq
  - is-01m10a6557hg7z3f06h36fah3b
  - is-01m10a69rjt2p1aby2a47tfq1h
created_at: 2026-08-26T23:52:19.734Z
updated_at: 2026-08-27T01:46:33.272Z
closed_at: 2026-08-27T01:46:33.271Z
close_reason: "Completed the coordinated first-party release train: kash-shell 0.4.8, kash-docs 0.2.6, kash-media 0.4.6, and deep-transcribe 0.1.12 are released from merged main commits with CI, package metadata, fresh-install, upgrade-shape, and installed-artifact validation. The nonblocking local uv build-selection issue remains tracked under the broader polish epic."
resolution: null
duplicate_of: null
---
Publish coordinated first-party patches through the final repaired stack: kash-shell 0.4.8, kash-docs 0.2.6, kash-media 0.4.6, and deep-transcribe 0.1.12. Intermediate 0.4.7, 0.2.4/0.2.5, and 0.4.5 releases established and exposed the shared-package initializer regression. Every final release must pass local and remote gates, use the authorized first-party cool-off exemption, publish from an immutable main commit, and pass PyPI metadata plus fresh and upgrade-shaped installed-artifact smoke tests.
