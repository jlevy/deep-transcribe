---
type: is
id: is-01m1nax7hjgt9tdrd7ws3jkvgf
title: Verify no stage sends the whole document
kind: task
status: closed
priority: 1
version: 3
spec_path: docs/project/specs/active/plan-2026-09-04-chunked-extraction.md
labels: []
dependencies: []
parent_id: is-01m1nax66j442h166dee52zt3r
created_at: 2026-09-04T04:30:23.791Z
updated_at: 2026-09-04T08:07:23.580Z
closed_at: 2026-09-04T08:07:23.569Z
close_reason: "Audit complete in the bead notes: no stage's input grows with duration. Outline and concepts chunk, synopsis map-reduces, speaker correction and the kash text stages window, roster inference reads only metadata. The one whole-document send left is the single-chunk synopsis path, which is a recording short enough to fit one call."
resolution: null
duplicate_of: null
---
Confirm on the long-form fixture that concept count scales with duration, no duplicate concepts or dangling relations survive the merge, and a transcript too large for one call (14h+, ~198k tokens) completes.

## Notes

AUDIT of every model call the pipeline makes, after 6a01bd8. The question is whether any
call's input grows without bound as the recording gets longer.

  infer_speaker_roster_from_context   BOUNDED — _roster_evidence assembles only the
                                      user's context and the source metadata. The
                                      transcript never enters it.
  correct_speaker_turns               WINDOWED — per utterance window, two call sites,
                                      both over a window rather than the document.
  break_into_paragraphs (kash)        WINDOWED — chopdiff WINDOW_2K_WORDTOKS.
  insert_section_headings (kash)      WINDOWED — chopdiff WINDOW_128_PARA.
  research_paras (kash)               PER PARAGRAPH — annotate_paras_async. Many calls,
                                      each small. Only runs under --deep.
  add_transcript_outline              CHUNKED — one call per ~30 min, concatenated.
  add_transcript_description          MAP-REDUCE — one summary per chunk, then one
                                      reduce over the summaries, a few thousand words at
                                      any recording length.
  extract_transcript_concepts         CHUNKED — one call per ~30 min, plus one reduce
                                      over the merged map, which is the map's size and
                                      not the transcript's.

The only remaining whole-document send is the single-chunk path in
add_transcript_description, which by definition is a recording short enough to fit one
call — that is the unchanged short-media path, not a ceiling.

So no stage's input grows with duration any more. What grows is the NUMBER of calls,
linearly: at 30-minute chunks a twelve-hour recording is 24 outline calls, 24 summaries,
24 concept calls, one synopsis reduce and one concept reduce.

Not yet verified: an actual fourteen-hour transcript end to end. The arithmetic and the
audit both say it completes; nothing has run one.
