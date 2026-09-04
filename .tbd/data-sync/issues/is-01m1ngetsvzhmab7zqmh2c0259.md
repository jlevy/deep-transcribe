---
type: is
id: is-01m1ngetsvzhmab7zqmh2c0259
title: Frame images are broken in every exported transcript
kind: bug
status: closed
priority: 0
version: 2
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T06:07:23.450Z
updated_at: 2026-09-04T06:17:04.053Z
closed_at: 2026-09-04T06:17:04.052Z
close_reason: "Fixed in 9f44191. Verified on the real 5.3-hour export served from a directory holding only the page and its assets: 502 of 502 frames load, zero broken, no reference to the upstream step's directory remains. Two tests cover the real shape (upstream assets + a derived doc in between) and the minified path; both fail without the fix."
resolution: null
duplicate_of: null
---
Every frame capture is a broken image in the exported HTML. This is not long-form
specific — it reproduces on the 22-min SNL example too.

MEASURED, loaded over http from the workspace root:
  Lex #501 export: 502 of 502 img.frame-capture have naturalWidth 0.
  SNL export: same refs, same missing directory (15 frames).

WHY:
  insert_frame_captures writes images into its own sidematter, e.g.
    docs/watch_step13_insert_frame_captures_1.doc.assets/
  and writes body refs relative to that directory. Two stages then derive new docs
  from it — extract_transcript_concepts and attach_transcript_index — each via
  item.derived_copy(), which does not carry sidematter. Those refs keep pointing at the
  frame-capture step's directory, which still works inside docs/ only because the
  directories are siblings.

  At export, kash's copy_item_sidematter(input_item, result_item) copies the INPUT
  item's own assets and rewrites old_prefix -> new_prefix. The input item is
  attach_transcript_index_*, which has no assets dir, so nothing is copied and the
  rewrite never matches the frame-capture prefix already in the body. The export lands
  in exports/ with refs to a directory that exists only under docs/.

  test_format_results_copies_frame_assets passes because it puts the frame in the
  source item's OWN assets dir — the one case the real pipeline never produces.

FIX, one of:
  a. Carry sidematter forward in the two deep-transcribe stages that derive from the
     frame-capture doc, so each derived doc owns its assets. Simple, but copies ~115 MB
     twice on a 5-hour run.
  b. Resolve and copy once at export time: in format_results, walk upstream to the
     frame-capture item, copy its assets into the export's assets dir, and rewrite the
     body prefix. One copy, and it is the step that actually needs the files co-located.
  (b) is preferred.

The test must be rewritten to exercise the real shape: frames in an UPSTREAM item's
assets, at least one derived doc in between, then assert the export's own assets dir
holds the file and the body points at it. Verify by loading the export over http from a
directory that contains only the export and its assets — no workspace around it.

Blocks the standalone export epic (dt-aa3m): a bundle cannot be portable while the
in-workspace export is already broken.
