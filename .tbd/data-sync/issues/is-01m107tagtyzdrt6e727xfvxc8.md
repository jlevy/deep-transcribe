---
type: is
id: is-01m107tagtyzdrt6e727xfvxc8
title: Release the first-party transcription stack
kind: epic
status: open
priority: 1
version: 6
labels: []
dependencies: []
parent_id: is-01m0zpq37wdhx51829qx0xmf0t
child_order_hints:
  - is-01m107q73p72w6xhebb6jr66tv
  - is-01m107q7cbhybbteyqfxg4esyq
  - is-01m107q7mqbhw6gb5cjqax4vhs
  - is-01m107q7x6bxhqwhqqgg10hx6j
  - is-01m107za1769d9gk5t29g48nyq
created_at: 2026-08-26T23:52:19.734Z
updated_at: 2026-08-26T23:55:03.078Z
---
Publish coordinated patch releases in dependency order: kash-shell 0.4.7, kash-docs 0.2.4, kash-media 0.4.5, and deep-transcribe 0.1.12. Each release must pass local and remote gates, use the authorized first-party cool-off exemption for same-day downstream pins, publish from an immutable main commit, and pass PyPI metadata plus installed-artifact smoke tests.
