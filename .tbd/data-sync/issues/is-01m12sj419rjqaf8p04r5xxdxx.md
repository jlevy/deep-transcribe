---
type: is
id: is-01m12sj419rjqaf8p04r5xxdxx
title: Derive the example's cast context instead of hand-writing it
kind: feature
status: open
priority: 2
version: 2
labels: []
dependencies: []
parent_id: is-01m0zpq37wdhx51829qx0xmf0t
created_at: 2026-08-27T23:40:54.176Z
updated_at: 2026-08-27T23:44:42.014Z
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
