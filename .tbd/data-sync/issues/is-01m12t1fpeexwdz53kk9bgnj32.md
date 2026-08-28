---
type: is
id: is-01m12t1fpeexwdz53kk9bgnj32
title: Declare kash-shell in deep-transcribe, which imports it directly
kind: task
status: closed
priority: 2
version: 2
labels: []
dependencies: []
parent_id: is-01m0zpq37wdhx51829qx0xmf0t
created_at: 2026-08-27T23:49:17.637Z
updated_at: 2026-08-28T04:20:12.343Z
closed_at: 2026-08-28T04:20:12.342Z
close_reason: deep-transcribe now declares kash-shell>=0.4.10,<0.5 directly, shipped in v0.1.14. It imports kash core throughout and now depends on the provider-routing fix, so the dependency is real rather than incidental.
resolution: null
duplicate_of: null
---
deep-transcribe imports kash core directly (from kash.exec import prepare_action_input, kash_runtime; from kash.model import Format, ItemType, StorePath, Item; from kash.config.setup import kash_setup; kash.web_gen, kash.workspaces, kash.actions.core.minify_html) but declares no kash-shell dependency. It gets one only because kash-media pulls kash-docs which pulls kash-shell.

This is the same undeclared-import gap fixed in kash-media by jlevy/kash-media#11, and it has the same failure mode: nothing in deep-transcribe's own metadata stops a resolver from pairing it with a kash-shell that lacks an API it calls.

Lower severity than the kash-media case, because deep-transcribe reads the new discovery fields defensively through .get() with isinstance guards rather than passing them as constructor arguments. So today this is a correctness-of-metadata issue, not a crash.

Fix: uv add --exclude-newer "14 days" "kash-shell>=0.4.10,<0.5" once that release exists, alongside the kash-media floor bump tracked in dt-31wq.
