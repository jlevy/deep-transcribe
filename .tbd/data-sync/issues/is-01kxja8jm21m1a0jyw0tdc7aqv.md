---
type: is
id: is-01kxja8jm21m1a0jyw0tdc7aqv
title: Audit and improve self-contained HTML transcript exports
kind: task
status: closed
priority: 2
version: 4
labels: []
dependencies: []
parent_id: is-01kxj4xxyfwmxmk3z9mebcf92x
created_at: 2026-07-15T07:18:36.417Z
updated_at: 2026-07-15T07:26:43.698Z
closed_at: 2026-07-15T07:26:43.697Z
close_reason: Completed deterministic audit of generated HTML, sibling assets, kash templates, and tminify output; created implementation children dt-a5iy, dt-g786, and dt-z68d under epic dt-zf97.
---
Determine whether exported static HTML can be forwarded as a single file and works offline. Audit scripts, styles, fonts, frame images, and other external references; document current guarantees and identify practical improvements such as inlining assets or producing a portable bundle.

## Notes

Audit result: current minified export is self-contained for compiled Tailwind CSS and page JavaScript, but not as a lone file. The SNL sample HTML is 132,170 bytes and references 15 sibling JPEG frames totaling about 15 MB; the local recording export is 371,896 bytes and references 144 sibling frames totaling about 24 MB. Both retain six external WOFF2 font URLs and the Feather JS CDN plus preconnect hints. Therefore HTML plus its matching .assets directory is forwardable as a folder/ZIP, with fonts/icons degraded offline; HTML alone loses frame captures and makes load-time CDN requests. Recommended implementation is explicit portable single-file output for bounded exports plus ZIP fallback for large outputs, inline SVG icons, system fonts by default, no embedded source media, and artifact-graph regression tests.
