# Deep Transcribe Guide

Deep Transcribe turns a media URL or local audio or video file into a cached transcript,
processed Markdown, and browser-ready HTML. This guide is packaged with the CLI so the
documentation always matches the installed release.

## Start Here

Inspect the command surface before running a transcription:

```shell
deep-transcribe --help
deep-transcribe --models
```

If Deep Transcribe is not installed, use the simple `uvx "deep-transcribe[youtube]"`
form in the current README. Automated agent workflows should follow the discovery and
version-matching guidance in the installed skill.

Deep Transcribe requires `ffmpeg`, `DEEPGRAM_API_KEY`, and the key for the selected LLM
profile: `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`. It reads `.env` and `.env.local` files
from the working-directory hierarchy and the user’s home directory.
Verify that key names exist without printing their values.

For YouTube sources, use the `youtube` extra, which supplies the Deno runtime yt-dlp
needs to solve current media challenges.

## Run a Transcription

The default `--annotated` preset identifies speakers, formats paragraphs and timestamps,
adds headings, a summary and description, captures representative video frames, and
exports HTML:

```shell
deep-transcribe \
    --workspace ./output \
    --annotated \
    --json \
    INPUT
```

`INPUT` may be a YouTube or other media URL, or a local audio or video path.
Use the same spelling of the source and the same workspace on later runs so the cache
identity stays stable.

Choose the least expensive preset that produces the requested result:

| Preset | Result |
| --- | --- |
| `--basic` | Raw diarized speech-to-text only |
| `--formatted` | Speaker names, paragraphs, and timestamps |
| `--annotated` | Formatting, sections, a synopsis, a structural outline, frames, and HTML |
| `--deep` | Annotated output plus researched paragraph notes |

Use `--with STAGE[,STAGE]` to add individual stages to a preset.
Run `deep-transcribe --help` for the current stage list and Deepgram model options.

## Long Recordings

Hours-long sources work end to end.
The longest recording verified through the whole pipeline is a five-and-a-quarter-hour
interview. Nothing in the design imposes a ceiling below twelve hours, but no recording
that long has been run yet, so treat twelve hours as the design target rather than a
tested limit. Every stage whose cost grows with duration is windowed or chunked, so a
twelve-hour recording is expected to take roughly four hours of wall time and to stay
inside every provider cap by a wide margin.

Nothing about the transcript is chunked or stitched together.
Speech-to-text sends the audio as a single request, so timestamps come back on one
continuous timeline rather than being reconciled across segment boundaries.
The cost of preparing that audio is flat in duration, because conversion streams through
ffmpeg rather than decoding the recording into memory.

Two practical notes for long sources:

- Downloads are sized for the job.
  Video is fetched at up to 1080p in H.264, which remuxes without re-encoding and keeps
  a multi-hour download to a couple of gigabytes rather than ten.
  Only the frame-capture stage needs video at all.
  Free space on the workspace volume is checked before the download and again before
  frame capture, and a run that would not fit stops with a message naming the volume and
  the sizes rather than filling the disk partway through.
- The request budget for speech-to-text scales with the length of the audio, so a long
  recording is not cut off by a timeout meant for short clips.

Expect the wall-clock time of a long run to be dominated by downloading and by the LLM
stages, not by speech-to-text: a five-hour recording transcribes in about a minute.

## Supply Recording Context

Raw media often lacks the names, roles, vocabulary, and chronology needed for accurate
speaker labels. Describe those facts in ordinary prose:

```shell
deep-transcribe \
    --title "Hotel Check In — SNL" \
    --context "This is the Saturday Night Live sketch Hotel Check In. The five speaking roles are Mr. Adams (Mikey Day), the Front Desk Employee (Kumail Nanjiani), the Government Representative (Beck Bennett), and two unnamed Room 904 Guests (Chris Redd and Leslie Jones). Label the unnamed roles Room 904 Guest (Chris Redd) and Room 904 Guest (Leslie Jones)." \
    --instructions "Write two short synopsis paragraphs. In the first, identify the SNL sketch and name all five performers with their roles. In the second, explain how the escalating hotel sales pitches drive the joke. Give every outline section exactly two concise bullets." \
    INPUT
```

The speaker-identification model uses the context and transcript to produce its internal
speaker-ID mapping.
When the prose clearly names the complete set of speaking roles, Deep
Transcribe also derives the internal roster needed to repair merged diarization
boundaries. The user does not need to write either structure.
Use `--context-file` for longer context or notes that will be revised across reruns:

```text
This is the Saturday Night Live sketch Hotel Check In.
Mr. Adams is played by Mikey Day, and the Front Desk Employee is played by Kumail
Nanjiani. Beck Bennett plays the Government Representative; Chris Redd and Leslie Jones
play the two unnamed Room 904 Guests.
Label the unnamed roles Room 904 Guest (Chris Redd) and Room 904 Guest (Leslie Jones).
```

Pass that file with `--context-file recording.txt`.

Use `--context` for facts about the recording: identities, roles, chronology,
terminology, and subject matter.
Use `--instructions` for trusted requests about the derived output, such as emphasis,
structure, or level of detail.
Keeping them separate lets models treat source metadata as evidence without accidentally
following instructions embedded in fetched metadata.
Instructions stick to the source: they are stored with it, so a later run without the flag
still follows them.
Pass `--instructions none` to drop them and go back to the default output.
For supported URL inputs, the media extractor fetches the source title, description,
canonical URL, and available channel and publication fields.
Deep Transcribe includes a bounded version automatically as reference evidence.
A cached URL resource created without extractor metadata is enriched once on its next
run. Use `--context` for relevant facts the publisher did not include or that require
review, such as a complete cast-to-role mapping.

The speaker roster step reads that metadata alongside your context, and is told which
evidence came from you and which was fetched from the source service.
It may state only what one of those supports.
`--web-search` additionally lets it corroborate facts it finds; it is off by default
because search can mislead.
Local files have no metadata to fetch and nothing to corroborate, so context is the only
evidence there.

`--title`, `--description`, and repeatable `--key-term` flags provide simple exact
values without a schema.
`--metadata YAML_OR_JSON` remains available for automation and advanced overrides.
Use `--speaker ID=NAME` only after verifying that a provider ID consistently belongs to
one speaker. Use the repeatable `--speaker-role` override only when the prose is
ambiguous or the inferred complete roster needs an exact correction.
Do not guess names that are not supported by the recording context.

## Iterate Without Repeating Speech-to-Text

A Deep Transcribe workspace is a reusable computation graph.
The useful workflow is:

1. Transcribe once.
2. Inspect the Markdown and rendered HTML.
3. Add context, correct speaker evidence, add processing instructions, change a model
   profile, or request another processing feature.
4. Rerun the same source in the same workspace.
5. Verify both cache reuse and output quality.

The normal cache-aware rerun resumes at the first affected action.
Do not delete the workspace, change its path, or change the source spelling between
iterations.

### Choose the Smallest Rerun

| Desired change | What to run | Speech-to-text behavior |
| --- | --- | --- |
| Change the title, description, context, instructions, or speaker overrides | Run the same command normally | Reuses the cached transcript |
| Edit a segment in a hints file the source already carries | Run the same command with `--segments PATH` | Reuses everything through section headings and resumes at the outline; about 20 minutes on a five-hour recording |
| Give a source its first hints file | Run the same command with `--segments PATH` | Reuses the cached transcript and speaker correction; repeats paragraph formatting and section headings once, about 45 minutes on a five-hour recording |
| Stop honoring stored hints or instructions | Run the same command with `--segments none` or `--instructions none` | Reuses the cached transcript |
| Add `--with STAGE` or move to a richer preset | Run the expanded command normally | Reuses the cached transcript and compatible processing |
| Change the saved Anthropic/OpenAI profile or deliberately regenerate all model-derived output | Add `--rerun-processing` | Reuses the cached transcript and forces later stages |
| Change `key_terms`, language, transcription model, or diarization model | Run normally with the new recognition input | Creates a new transcript cache entry |
| Deliberately repeat every action | Add `--rerun` | Makes a new paid speech-to-text request |

Do not add `--rerun-processing` merely because metadata changed.
Metadata participates in semantic cache identity, so a normal rerun already invalidates
the first affected model stage and everything that depends on it.
Processing instructions are excluded from speaker correction, paragraph formatting, and
section-generation cache identity, so changing only those instructions resumes at the
synopsis and outline stages.

Use `--rerun-processing` when inputs outside the item metadata changed, such as a saved
model profile, or when a complete semantic regeneration is the actual goal.
Use `--rerun` only when a fresh Deepgram result is wanted.

### Set Aside Parts That Are Not the Conversation

A long recording is often not all conversation.
Many podcasts open with a highlight reel cut from the interview that follows, break for
read advertisements, and close with an outro.
Those stretches distort the analysis: a teaser is the same words as the moments it
previews, so leaving it in counts them twice, and an ad read is not about the
conversation at all.

Mark them in a hints file and pass it with `--segments`:

```yaml
segments:
  - at: "0:00:00 - 0:01:48"
    purpose: teaser
    note: "Highlight reel; the interview starts after it"
  - at: "1:12:30 - 1:14:05"
    purpose: promo
```

`purpose` is one of `teaser`, `intro`, `promo`, `outro`, or `other`, and any other word is
an error naming the ones that work.
It is a closed set rather than a free label because the purpose decides both whether the
stretch is left out of the analysis and what the collapsed block is called, so a word
quietly read as `other` would change the run without saying so.
Times read as `H:MM:SS`, `MM:SS`, or plain seconds, and a span may also be written as
separate `start` and `end`.
Suppression follows the purpose — teaser, promo and outro are left out of the analysis,
an intro is kept because it is short and genuinely about the conversation — and
`suppress: true` or `false` overrides that for one entry.

Suppressed stretches are **set aside, not deleted**.
The concept map, outline and synopsis do not read them; the transcript still contains
every word, collapsed behind a line naming what it is, and prints expanded.

Hints stick to the source, so a later run without `--segments` still honors the last file
you passed.
To go back to a recording with nothing set aside, pass `--segments none`, which removes the
stored hints instead of reading a file.

The rerun is cheap by design.
Hints join the pipeline at the same point as processing instructions, so transcription,
speaker correction, paragraph formatting and section headings all keep their cache
identity, and only the analysis and the page are rebuilt.
Editing a hint and rerunning a five-hour recording costs minutes, not a fresh pipeline.

When a run finds an opening that repeats later, it writes `segments.suggested.yml` into
the workspace and says so.
That file is a draft to review, never applied on its own, and a run that already has
hints does not overwrite it.
The intended loop is: run, look at the output, revise the hints, run again — which an
agent can drive as readily as a person.

### Correct a Reviewed Result

After reviewing the first output, revise the prose context and repeat the command:

```shell
deep-transcribe \
    --workspace ./output \
    --annotated \
    --context-file ./recording.txt \
    --json \
    INPUT
```

Ordinary mislabeling should be corrected by adding the participants, roles, chronology,
or forms of address to the prose context.
For a true diarization boundary error, where one provider ID contains several people or
one person has several IDs, state the complete set of speaking roles in that prose.
Deep Transcribe derives the roster, then corrects timestamped turns with the careful
model profile while preserving the raw provider transcript for review.
Repeated `--speaker-role` flags remain an exact fallback when a reviewed inference needs
an override.

For an output correction, pass `--instructions`. Annotated output places a short
two-paragraph synopsis first, then an always-visible sans-serif outline.
The outline follows the transcript’s section headings when they are useful and gives
concise key points for each section.

```shell
deep-transcribe \
    --workspace ./output \
    --annotated \
    --context-file ./recording.txt \
    --instructions "Emphasize decisions and unresolved questions." \
    --json \
    INPUT
```

For a new feature, extend the existing command instead of starting over:

```shell
deep-transcribe \
    --workspace ./output \
    --annotated \
    --with research_paras \
    --metadata ./recording.yml \
    --json \
    INPUT
```

To compare model providers against the same raw transcript:

```shell
deep-transcribe \
    --models openai \
    --workspace ./output \
    --annotated \
    --rerun-processing \
    --metadata ./recording.yml \
    --json \
    INPUT
```

Use the same command with `--models anthropic` to switch back.

### Verify Cache Reuse

Inspect the workspace log before and after a semantic-only rerun:

```shell
rg -n 'Video transcript already in cache|Transcribing via Deepgram' \
    ./output/logs/workspace.log
```

A semantic-only rerun should report a transcript cache hit, and the Deepgram request
count should not increase.
Then inspect the transcript and HTML at the beginning, middle, and end.
Check speaker continuity, missing speech, timestamps, headings, synopsis, outline,
annotations, and frame captures.
Timestamps are muted bracketed text.
Supported web sources receive time-specific links, and YouTube links open an embedded
player.
Local audio and video timestamps are intentionally not linked because a `file://`
URL cannot seek reliably.
A zero exit status confirms execution, not transcription quality.

### Recover From a Failed Stage

Keep the workspace and rerun the same command after fixing the failure.
Completed upstream actions remain reusable, while the incomplete action runs again.
Check the workspace log before broadening the rerun scope.
Deleting the workspace discards the recovery point.

### Agent Prompt Pattern

An agent can run the review-and-correct loop from this compact request:

> Inspect the existing Deep Transcribe result for `INPUT` in `WORKSPACE`. Update the
> private metadata file with `CORRECTIONS` and any requested processing instructions,
> rerun the same preset without `--rerun-processing` or `--rerun`, and verify that the
> Deepgram request count did not increase.
> Review the corrected transcript and rendered HTML at the beginning, middle, and end,
> then report the final artifact paths.
> Keep source-specific names, paths, and content out of the repository.

Ask for `--rerun-processing` when the requested change is a model-profile comparison or
a deliberate full semantic refresh.
Ask for `--rerun` only when a new speech-to-text result is wanted.

## Inspect Outputs

Each successful run reports:

- the workspace containing cached media and intermediate results;
- the final transcript source; and
- browser-ready HTML.

Use `--json` when another tool or agent needs stable artifact paths.
Open the workspace with `kash` when intermediate items or action history require deeper
inspection.

### Save the HTML as a PDF

The HTML export is the presentation source.
Its print stylesheet switches to a light page, hides interactive controls, keeps
transcript elements together when practical, and adds the Deep Transcribe footer.

To create a PDF without adding a renderer dependency:

1. Open the final HTML in a modern browser.
2. Choose **Print → Save as PDF**.
3. Use 100% scale, disable the browser’s headers and footers, and enable background
   graphics.
4. Inspect the title and outline, a transcript page with frame captures, and the final
   page before sharing the PDF.

An installed Chrome or Chromium executable can make the same browser print reproducible.
Replace the placeholder with the absolute path Deep Transcribe reports:

```shell
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --headless=new \
    --disable-background-networking \
    --no-pdf-header-footer \
    --print-to-pdf=transcript.pdf \
    "file:///absolute/path/to/transcript.html"
```

Use `google-chrome` or `chromium` as the executable on other platforms.

An agent should use the same browser-print workflow through its browser controls or an
installed Chrome or Chromium executable.
Keep the HTML and its adjacent asset directory together so local frame captures load.
Do not substitute a non-browser HTML-to-PDF converter: browser CSS, font metrics, and
list markers can render differently.

Keep private metadata beside the source media or in another private directory.
Do not copy private paths, participant names, transcript content, or credentials into
repository code, tests, docs, commits, pull requests, or issue records.

## Select a Model Profile

Inspect or change the workspace’s Anthropic/OpenAI role mapping:

```shell
deep-transcribe --models
deep-transcribe --models anthropic --workspace ./output
deep-transcribe --models openai --workspace ./output
```

New workspaces use the Anthropic profile by default.
`deep-transcribe --models` prints the exact current models and the active profile.

## Install the Agent Skill

Deep Transcribe can print and install its own agent skill:

```shell
deep-transcribe --skill
deep-transcribe --install-skill
```

Run `--install-skill` from a project root.
By default it writes the portable `.agents/skills/deep-transcribe/` bundle, the
`.claude/skills/deep-transcribe/` mirror, and a marker-bounded block in `AGENTS.md`. The
operation is idempotent and refuses to overwrite artifacts stamped with a newer format
than the installed CLI understands.

Select project-local surfaces explicitly when needed:

```shell
deep-transcribe --install-skill --surfaces=portable,agents-md
deep-transcribe --install-skill --surfaces=claude
```

For a deliberate global or custom single-base install:

```shell
deep-transcribe --install-skill --agent-base ~/.codex
deep-transcribe --install-skill --agent-base ~/.claude
```

`--agent-base` writes `skills/deep-transcribe/` under the supplied directory and cannot
be combined with `--surfaces`.

If Deep Transcribe is not installed yet, install the public discovery skill from the
repository:

```shell
npx skills add jlevy/deep-transcribe@deep-transcribe
```

The discovery skill uses a local executable when available and otherwise bootstraps an
exact version-pinned `uvx` runner.

## Troubleshooting

- Run `deep-transcribe --help` before changing transcription options.
- Preserve the workspace after a failure so completed work remains reusable.
- Confirm `ffmpeg` is on `PATH` and that the `youtube` extra is installed when media
  acquisition fails.
- Confirm required key names exist without echoing their values.
- Use `--json` for machine-readable artifact paths and errors.
- Inspect the workspace log before deciding that a paid stage must be repeated.
- Run `deep-transcribe --skill` when an agent needs the current operational contract.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
