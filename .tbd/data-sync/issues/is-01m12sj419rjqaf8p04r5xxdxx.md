---
type: is
id: is-01m12sj419rjqaf8p04r5xxdxx
title: Derive the example's cast context instead of hand-writing it
kind: feature
status: open
priority: 2
version: 11
labels: []
dependencies: []
parent_id: is-01m0zpq37wdhx51829qx0xmf0t
created_at: 2026-08-27T23:40:54.176Z
updated_at: 2026-08-28T04:21:18.030Z
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
CAN IT BE DERIVED? Three checks, 2026-08-27.
1. YouTube metadata cannot supply the gap. Dumped all yt-dlp fields for the video (60 non-empty). The string 'Bennett' appears zero times anywhere in the blob. Chris Redd, Leslie Jones, Mikey Day, and Kumail Nanjiani each appear, in tags and description, both of which we already capture in full (547-char description, 38 tags). 'chapters' is null. There is no cast or credits field. Beck Bennett is simply not in the source.
2. Model knowledge does not supply it either. Asked directly about the sketch by name, season, episode, and host, the model declined: 'I don't have confident, specific information about this particular SNL sketch... I cannot reliably list every speaking role and cast member for this specific Hotel Check In sketch without risking inaccuracies.'
3. A single roster call on metadata plus the diarized transcript both helps and hurts.
   Helps, and this is the important part: it independently identified that the diarizer merged two different roles into SPEAKER 0, the government agent at the open and the Room 904 guest mid-sketch. That merge is the direct cause of the five-to-three collapse measured above, and the model found it from the transcript alone.
   Hurts: it assigned the government representative to Chris Redd. That is wrong, and it is wrong in a specific way. Beck Bennett is absent from the tags, so the model reached for a name that was present. It anchored on the available options rather than recalling anything.
The control that failed matters for the design. The prompt already said 'If you are unsure of a performer, say unknown rather than guessing', and it guessed anyway. A prompt instruction is not sufficient protection.
Design implication:
- Derive structure from the transcript. Role count, turn boundaries, and merged-speaker detection are all derivable and are what actually fixes the roster.
- Do not let the model attach a performer name unless that name appears in source evidence AND the mapping is supported. Names present in tags are candidates, not assignments.
- Emit 'unknown' or a role-only label as a first-class output rather than a fallback, so a missing name degrades to 'Government Representative' instead of a confident wrong name.
- Surface the proposed roster for review before it is baked into the transcript, so a wrong guess is cheap to correct.
MECHANISM, and the agreed grounding rule.
infer_speaker_roster_from_context (src/deep_transcribe/speaker_correction.py:113) reads only item.additional_context and returns early when it is empty. It never sees the extractor metadata. Its system message is 'You conservatively structure user-authored speaker context without adding facts.' So the URL-only run did not produce a bad roster, it produced no roster at all, and speaker assignment ran unanchored. That is the whole five-to-three collapse.
The two downstream prompts, _assign_window and _adjudicate_conflicts, both assign to a fixed roster and both already say to use UNKNOWN rather than guessing. They are not the risk. The risk is entirely in whatever creates the roster.
Grounding rule for the roster prompt, per the user:
- Include a name only when it is present in data on hand, meaning user-supplied context or YouTube metadata (description, tags, channel, title), or corroborated by web search when that is enabled.
- Anything not so supported stays a role-only label such as 'Government Representative', or 'unknown'. Role-only is a first-class result, not a degraded one.
- Tags are a candidate pool, never an assignment. The measured failure was the model taking 'Chris Redd' from the tag list for a role Beck Bennett actually played, purely because Bennett was absent and Redd was present.
- State the rule as a hard constraint on output, not as advice. The failing control run already carried 'If you are unsure of a performer, say unknown rather than guessing' and guessed regardless, so the instruction must be paired with a check that every emitted name appears in the supplied evidence.
Optional web search:
- Off by default; opt-in flag. When on, a name may also be included if corroborated by a retrieved source, and the roster should carry the corroborating source so a wrong mapping is traceable.
- Feasible without new accounts: EXA_API_KEY, PERPLEXITYAI_API_KEY, and FIRECRAWL_API_KEY are already present in the user's environment. Note that kash's research_paras is LLM-only today, so there is no existing web-search path in the pipeline to reuse.
Scope note: extending roster inference to read metadata under this rule is self-contained and testable against the baselines recorded above (three of five speakers with metadata alone, five of five with one sentence of context). Web search is a separate, larger increment.
WEB SEARCH WORKS, AND THE GUARD I PROPOSED DOES NOT.
Anthropic server-side web search (tool web_search_20250305, claude-opus-4-5) answered the question the metadata cannot: 17.2 seconds, three queries, landed on SNL Transcripts, and returned Beck Bennett as the government representative plus the full five-person cast. So the optional-search branch is viable today with no new provider account. Perplexity was tried first and is out of quota.
Correction to the earlier design note. The proposed code guard, 'every name in a roster label must appear in the supplied evidence', would NOT have caught the observed failure. 'Chris Redd' was present in the tags. The error was attaching a present name to the wrong role. Presence is checkable; the role-to-name mapping is not, and that is where the failure lives.
What is actually mechanically checkable:
- Association, not presence. Accept a name only when the evidence itself associates it with that role, as the description does for 'front desk employee (Kumail Nanjiani)'. This would have blocked 'Government Representative (Chris Redd)', because nothing in the metadata ties Redd to that role. Stricter than presence and it catches the real failure.
- Citation required. With search enabled, require a retrieved source per name and store it, so a wrong mapping is traceable rather than anonymous.
- Review before bake-in. Surface the proposed roster so a wrong mapping is cheap to correct.
Truth of the mapping is not verifiable in code. Beyond the checks above it is prompt discipline plus residual risk, and that should be stated rather than papered over.
SETTLED SPEC:
1. Take the fetched metadata by default. Tell the model where it came from, that it is fetched from the video platform, and that odd or hostile metadata is possible. Escaping and length bounds already exist in source_prompt_context.
2. Never assert anything not present in the source. Unsupported roles stay role-only labels.
3. No web search unless explicitly enabled, since search can mislead. Default off.
IMPLEMENTED (pending end-to-end validation).
- transcription_metadata.py: escape_evidence and source_service_name helpers; source_prompt_context gained include_user_context so the roster prompt can label the two evidence sources separately.
- speaker_correction.py: ROSTER_INFERENCE_PROMPT rewritten. It no longer says 'Do not use fetched source metadata'. Each evidence block is labeled with its origin, user-written or 'Fetched automatically from YouTube', with a note that published metadata is often incomplete or unrelated. One prohibition sentence: use only that evidence, do not add any other facts, and name a performer only where the evidence ties that performer to that role.
- infer_speaker_roster_from_context now runs on metadata alone, not just user context, and takes web_search.
- transcribe_commands.py: the caller no longer gates on additional_context, so metadata-only sources reach the roster step.
- CLI: --web-search, off by default, applied after preset resolution so presets cannot clear it. Threaded through TranscribeOptions.web_search to llm_template_completion(enable_web_search=...), which kash already supports.
- Tests: metadata provenance and search-enabled paths, plus a no-evidence case that must not call the model. 78 pass.
Expectation to check end to end: metadata alone will likely still return complete=false for this video, because four tagged names do not establish the complete speaking set. The win is that the step now sees the metadata at all and can succeed for sources that do list their speakers. Web search is the path that closes the SNL case.
END-TO-END RESULT. URL plus --web-search, clean workspace, no user context:
  Mr. Adams (guest checking in)  20 turns   (hand-written-context run: 21)
  Kumail (hotel clerk)           20         (21)
  Chris (hotel guest)             2         (2)
  Beck (escorting agent)          2         (2)
  Leslie (hotel guest)            1         (1)
All five roles, turn counts within one of the reviewed result, derived from metadata plus search plus the transcript with nothing supplied by hand. Baseline for comparison is three speakers from a bare URL.
Two defects were found and fixed while testing, both of which made the feature silently do nothing:
1. kash gates web search on litellm.supports_web_search, false for claude-sonnet-5, and then sets the OpenAI-style web_search_options that Anthropic ignores. The first end-to-end run logged 'Web search requested but not supported by model claude-sonnet-5' and behaved identically to no search. Fixed by routing on provider and passing Anthropic's server tool through kash's existing tools parameter, verified against litellm directly first.
2. The completeness test rejected cast lists outright, which is exactly what a search returns, so the step failed closed even once search worked. Loosened to accept a cast list whose members can be matched to speaking turns in the transcript the step already holds.
Remaining, and worth a follow-up rather than blocking: the derived labels use performer first names, 'Kumail (hotel clerk)', 'Beck (escorting agent)', where the curated run uses roles, 'Front Desk Employee', 'Government Representative'. Structure is right, style is not. Also seen in an isolated search probe: the model correctly named Beck Bennett but stated in passing that Mr. Adams was played by Chris Redd. Search lowers the error rate, it does not remove it, which is why it stays opt-in and why the roster remains reviewable.

RESOLVED IN PART by the shipped work. With kash-shell 0.4.10's working web search, the released v0.1.14 derives all five roles from a bare URL plus --web-search, and the label-style concern recorded above went away on its own: labels now come out as 'Mr. Adams (Mikey Day)', 'Front Desk Employee (Kumail Nanjiani)', 'Government Escort (Beck Bennett)' rather than performer first names. Better evidence produced better labels without a prompt change.

What remains for this bead is the no-search case: a bare URL with search off still yields three speakers, since metadata alone does not establish the complete speaking set. That is the baseline to beat.
