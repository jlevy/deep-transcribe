---
type: is
id: is-01m0zpr0xmy7y85tecbxew2mbk
title: Keep Kash initialization inside the selected local workspace
kind: bug
status: open
priority: 2
version: 1
labels: []
dependencies: []
parent_id: is-01m0zpq37wdhx51829qx0xmf0t
created_at: 2026-08-26T18:53:58.578Z
updated_at: 2026-08-26T18:53:58.578Z
---
Ensure Deep Transcribe configures Kash before import-time logging and cache initialization so the selected --workspace contains operational state instead of falling back to the home-directory global workspace.
