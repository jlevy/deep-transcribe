---
type: is
id: is-01m12sj419rjqaf8p04r5xxdxx
title: Derive the example's cast context instead of hand-writing it
kind: feature
status: open
priority: 2
version: 5
labels: []
dependencies: []
parent_id: is-01m0zpq37wdhx51829qx0xmf0t
created_at: 2026-08-27T23:40:54.176Z
updated_at: 2026-08-28T00:24:52.688Z
---
The README example passes a 90-word --context string naming all five performers and their roles, plus four --key-term flags. That is a lot of hand-authored structure for facts the pipeline can mostly reach on its own, and it makes the headline example look harder to use than the tool actually is.

Two sources are already available and unused for this:

1. Extractor metadata. As of the yt-dlp metadata work, the source resource carries title, description, channel, uploader, categories, and tags, and source_prompt_context already feeds a bounded version of these to the semantic stages. The SNL description names the sketch and the show.
2. A model call. The run already makes dozens of LLM calls. One more, given the title, description, channel, and the diarized transcript, could propose the speaker roster and likely key terms directly, then let the user correct it.

The asymmetry is the point: we ask a human to hand-assemble structured input for something we could ask a model once.

Work:
- Measure what the current example produces with --context dropped entirely, keeping only --title and --instructions, now that extractor metadata reaches the prompts. Compare speaker labels against the reviewed five-role result.
- If the roster degrades, prototype a roster-proposal stage that runs before speaker identification and writes its proposal into the workspace for review, rather than requiring it up front.
- Reconsider whether --key-term is needed in the example at all, or whether terms can be proposed from the description and transcript.
- Rewrite the README example to whatever the minimum is that still produces the reviewed output. Ideally the headline command is a URL, a title, and an instruction.

Keep --context as the override for facts the source does not publish; the goal is that it stops being mandatory for a good result.

## Notes

Shape agreed with the user: keep two examples rather than one.
- Quick example: effortless for YouTube. A URL, and little or nothing else. It should lean on the extractor metadata the source resource now carries (title, description, channel, uploader, categories, tags) and on the models already in the pipeline, rather than asking the user to hand-assemble a roster.
- Advanced example: keeps the rich --context and --key-term flags, for videos whose metadata is thin or absent, and for cases where the user wants to steer labels and terminology deliberately.
The current README example is the advanced one wearing the quick one's clothes. It is the first command a reader sees, which makes the tool look harder to use than it is.
Testing note (2026-08-27): rerunning in an existing workspace without --context does NOT test the no-context path. additional_context is persisted on the URL resource item (visible as additional_context: in workspace/resources/watch_1.resource.yml), so a rerun inherits the previously supplied context and reuses the whole cached pipeline, zero Deepgram calls. Measuring what metadata alone can do requires a clean workspace.
That persistence is reasonable for the documented review-and-rerun loop, but it means there is no way to clear stored context by omitting the flag, and it makes it easy to over-estimate how well a simplified command performs. Worth deciding whether an explicit way to clear context is needed.
MEASURED (2026-08-27, clean workspace snl-quick-test, command: --annotated plus the URL only, no --context, --key-term, --title, or --instructions):
Roster collapses from five speakers to three.
  Hotel Front Desk Employee  15 turns
  Mikey Day                  12 turns
  Government Official        11 turns
Zero occurrences of Chris Redd, Leslie Jones, or Beck Bennett in the output. Both Room 904 Guests are gone; their lines were absorbed into the three surviving labels. Labeling is also inconsistent, one performer name mixed with two role names.
The failure propagates into the synopsis, which becomes factually wrong: it reports that the government official 'briefly interrupts the front desk to request towels and make an unrelated flirtatious remark'. Those are the Room 904 Guests' lines, misattributed.
So the metadata is necessary but not sufficient. The description and tags do supply four of the five performer names and both are already fed to speaker_correction and transcript_overview via source_prompt_context, but nothing recovers the two short-interjection speakers or maps performers to roles. Simply deleting --context from the README example would showcase a worse result, not a simpler one.
This makes the roster-proposal stage the real work item rather than a documentation change. The pipeline has the raw material and a diarized transcript; what is missing is a step that asks a model to reconcile them into a roster before speaker identification runs.

MEASURED, compact context (same clean workspace, transcript reused, no new Deepgram request). Context reduced to 35 words naming the cast, with no --key-term, --title, or --instructions:

  Mr. Adams              20 turns   (reviewed run: 21)
  Front Desk Employee    19         (21)
  Room 904 Guest 1        2         (2, labeled 'Room 904 Guest (Chris Redd)')
  Government Rep          2         (2)
  Room 904 Guest 2        1         (1, labeled 'Room 904 Guest (Leslie Jones)')

All five roles recovered. The synopsis is factually correct, names all five performers, correctly attributes the Room 904 interruption, and picks up 'Chatsworth House, a Marriott experience', the Stargazer Lounge, and the Indulge spa with no --key-term flags. The only loss is cosmetic: unnamed guests come out as 'Room 904 Guest 1/2' rather than carrying the performer name, which is exactly what the dropped labeling instruction bought.

Conclusion, and what shipped in the README: the headline example now passes one --context sentence plus --annotated and the URL. The full command is kept below as a steering example and is the one behind the published PDF.

Remaining work for this bead is the part still not automatic: deriving the role mapping and the short-turn speakers without any human-supplied context. The measurements above are the baseline to beat, three of five speakers with metadata alone.
