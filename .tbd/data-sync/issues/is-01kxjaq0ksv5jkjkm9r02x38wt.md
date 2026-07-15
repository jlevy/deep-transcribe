---
type: is
id: is-01kxjaq0ksv5jkjkm9r02x38wt
title: Remove load-time CDN dependencies from transcript HTML
kind: task
status: open
priority: 2
version: 1
labels:
  - html
  - portability
dependencies: []
parent_id: is-01kxj4xxyfwmxmk3z9mebcf92x
created_at: 2026-07-15T07:26:29.496Z
updated_at: 2026-07-15T07:26:29.496Z
---
Remove load-bearing external font and Feather icon requests from portable transcript exports. Prefer inline SVG icons and a system font stack for the lean portable mode, with optional embedded WOFF2 only if fidelity justifies the size. Remove preconnects and add a CSP or equivalent validation that portable output makes no network requests.
