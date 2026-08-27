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

If Deep Transcribe is not installed, use the `uvx` command in the current README.
Automated agent workflows should use the exact version-pinned runner shown by the
installed skill.

Deep Transcribe requires `ffmpeg`, `DEEPGRAM_API_KEY`, and the key for the selected LLM
profile: `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`. It reads `.env` and `.env.local` files
from the working-directory hierarchy and the user’s home directory.
Verify that key names exist without printing their values.

For YouTube sources, install a JavaScript runtime such as Deno, Node.js, or Bun so
yt-dlp can solve current media challenges.

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

## Supply Recording Context

Raw media often lacks the names, roles, vocabulary, and chronology needed for accurate
speaker labels. Describe those facts in ordinary prose:

```shell
deep-transcribe \
    --title "Hotel check-in dialogue" \
    --context "The receptionist speaks first. The guest is Tom Sanders. He has a three-night reservation and receives a room upgrade." \
    --instructions "Keep the synopsis brief and organize the outline around the phases of check-in." \
    INPUT
```

The speaker-identification model uses the context and transcript to produce its internal
speaker-ID mapping. The user does not need to write that mapping.
Use `--context-file` for longer context or notes that will be revised across reruns:

```text
This is a two-person hotel check-in conversation.
The receptionist speaks first. The guest is Tom Sanders.
Tom has a three-night reservation and receives a room upgrade.
```

Pass that file with `--context-file recording.txt`.

Use `--context` for facts about the recording: identities, roles, chronology,
terminology, and subject matter.
Use `--instructions` for trusted requests about the derived output, such as emphasis,
structure, or level of detail.
Keeping them separate lets models treat source metadata as evidence without accidentally
following instructions embedded in fetched metadata.

`--title`, `--description`, and repeatable `--key-term` flags provide simple exact
values without a schema.
`--metadata YAML_OR_JSON` remains available for automation and advanced overrides.
Use `--speaker ID=NAME` only after verifying that a provider ID consistently belongs to
one speaker. Use the repeatable `--speaker-role` override only when the diarizer merged
or split voices and the careful boundary-correction stage needs a complete roster.
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
one person has several IDs, also give the complete roster with repeated `--speaker-role`
flags. Deep Transcribe then corrects timestamped turns with the careful model profile
while preserving the raw provider transcript for review.

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
- Confirm `ffmpeg` and a JavaScript runtime are on `PATH` when media acquisition fails.
- Confirm required key names exist without echoing their values.
- Use `--json` for machine-readable artifact paths and errors.
- Inspect the workspace log before deciding that a paid stage must be repeated.
- Run `deep-transcribe --skill` when an agent needs the current operational contract.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
