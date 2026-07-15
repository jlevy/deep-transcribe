---
type: is
id: is-01kxjar0zn3a684rf5qnb1nvcn
title: Fix invalid CSS selectors in transcript HTML minification
kind: bug
status: open
priority: 2
version: 1
labels:
  - html
  - css
dependencies: []
parent_id: is-01kxj4xxyfwmxmk3z9mebcf92x
created_at: 2026-07-15T07:27:02.644Z
updated_at: 2026-07-15T07:27:02.644Z
---
Tailwind v4.3.2 reports two optimizer warnings while compiling a real Deep Transcribe export: a pseudo-element followed by an attribute selector (.footnote::after[content*=...]) and an invalid selector beginning with a literal <style> token before [data-theme=dark]. Locate the source template/CSS generation bug, correct both selectors, and add coverage that compilation completes without CSS warnings.
