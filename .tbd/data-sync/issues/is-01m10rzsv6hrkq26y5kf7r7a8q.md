---
type: is
id: is-01m10rzsv6hrkq26y5kf7r7a8q
title: Run the SNL fixture and prove cache-aware refinement
kind: task
status: closed
priority: 1
version: 5
spec_path: docs/project/specs/active/plan-2026-08-26-snl-example-single-command-cli.md
labels: []
dependencies:
  - type: blocks
    target: is-01kxj4zkw8vp8g4ebs496hwdgw
parent_id: is-01m10ryb6ze39bmjjq0chrxpbx
created_at: 2026-08-27T04:52:25.061Z
updated_at: 2026-08-27T06:59:06.078Z
closed_at: 2026-08-27T06:59:06.077Z
close_reason: Reviewed SNL run distinguishes all five roles, produces the requested synopsis and outline, and reruns against released dependencies without another Deepgram or LLM stage.
resolution: null
duplicate_of: null
---
Run the official SNL Hotel Check In video with one reviewed prose context covering all five roles. Inspect title, synopsis, outline, labels, frames, HTML, and caches; refine context or instructions once and prove Deepgram is not called again.

## Notes

Live public run completed with one Deepgram call, five reviewed role labels, two synopsis paragraphs, a six-section/two-bullet outline, 16 frames, and 46 paragraph timestamps. The instruction-only rerun skipped raw transcription and every transcript-processing stage through section headings, resuming at the overview boundary. Remaining work is to land/release the cache fixes, rerun against released dependencies, and visually approve the HTML/PDF/README artifacts.
