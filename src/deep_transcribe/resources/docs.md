# Deep Transcribe Guide

Deep Transcribe turns a media URL or local audio or video file into a cached transcript,
processed Markdown, and browser-ready HTML. This guide is packaged with the CLI so the
documentation always matches the installed release.

## Start Here

Inspect the command surface before running a transcription:

```shell
deep-transcribe --help
deep-transcribe transcribe --help
deep-transcribe models --help
```

If Deep Transcribe is not installed, use the exact version-pinned runner shown by the
installed skill or the current README. Avoid an unpinned `@latest` or unconstrained
package invocation in agent workflows.

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
deep-transcribe transcribe \
    --workspace ./output \
    --annotated \
    --json \
    INPUT
```

The direct-source shorthand is also supported:

```shell
deep-transcribe --workspace ./output --annotated --json INPUT
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
Run `deep-transcribe transcribe --help` for the current stage list and Deepgram model
options.

## Supply Recording Context

Raw media often lacks the names, roles, vocabulary, and chronology needed for accurate
speaker labels. Supply reusable metadata instead of hoping a later model infers it.

```yaml
title: Hotel check-in dialogue
description: A receptionist checks a guest into a hotel.
additional_context: |
  This is a two-person hotel check-in conversation. The receptionist speaks first.
  The guest has a three-night reservation and receives a room upgrade.
processing_instructions: |
  Keep the synopsis brief. Organize the outline around the main phases of check-in.
key_terms:
  - Transnational Hotel
speaker_hints:
  "0": Hotel Receptionist
  "1": Hotel Guest
speaker_roster:
  - Hotel Receptionist
  - Hotel Guest
```

Pass it with `--metadata recording.yml`. The equivalent repeatable inline options are
`--context`, `--context-file`, `--instructions`, `--instructions-file`, `--key-term`,
`--speaker ID=NAME`, and `--speaker-role NAME_OR_ROLE`.

Use `additional_context` for facts about the recording: identities, roles, chronology,
terminology, and subject matter.
Use `processing_instructions` for trusted requests about the derived output, such as
emphasis, structure, or level of detail.
Keeping them separate lets models treat source metadata as evidence without accidentally
following instructions embedded in fetched metadata.

Use `speaker_hints` only when one provider speaker ID consistently belongs to one known
person or role.
Use a complete `speaker_roster` when the diarizer split one person across
IDs or merged multiple people under one ID. Describe roles, chronology, forms of
address, subject matter, or difficult dialogue transitions in `additional_context`. Do
not guess names that are not supported by the recording context.

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
| Change `title`, `description`, `additional_context`, `processing_instructions`, `speaker_hints`, or `speaker_roster` | Run the same command normally | Reuses the cached transcript |
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

After reviewing the first output, edit the private metadata file and repeat the command:

```shell
deep-transcribe transcribe \
    --workspace ./output \
    --annotated \
    --metadata ./recording.yml \
    --json \
    INPUT
```

For a diarization boundary error, give the complete roster and describe the speakers’
roles or the ambiguous transition in `additional_context`. Deep Transcribe then corrects
timestamped turns with the careful model profile while preserving the raw provider
transcript for review.

For an output correction, add `processing_instructions` to the same metadata file or
pass `--instructions`. Annotated output places a short two-paragraph synopsis first,
then an always-visible sans-serif outline.
The outline follows the transcript’s section headings when they are useful and gives
concise key points for each section.

```shell
deep-transcribe transcribe \
    --workspace ./output \
    --annotated \
    --instructions "Emphasize decisions and unresolved questions." \
    --metadata ./recording.yml \
    --json \
    INPUT
```

For a new feature, extend the existing command instead of starting over:

```shell
deep-transcribe transcribe \
    --workspace ./output \
    --annotated \
    --with research_paras \
    --metadata ./recording.yml \
    --json \
    INPUT
```

To compare model providers against the same raw transcript:

```shell
deep-transcribe models --workspace ./output --set openai
deep-transcribe transcribe \
    --workspace ./output \
    --annotated \
    --rerun-processing \
    --metadata ./recording.yml \
    --json \
    INPUT
```

Use `--set anthropic` to switch back.

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

Keep private metadata beside the source media or in another private directory.
Do not copy private paths, participant names, transcript content, or credentials into
repository code, tests, docs, commits, pull requests, or issue records.

## Select a Model Profile

Inspect or change the workspace’s Anthropic/OpenAI role mapping:

```shell
deep-transcribe models
deep-transcribe models --workspace ./output --set anthropic
deep-transcribe models --workspace ./output --set openai
```

New workspaces use the Anthropic profile by default.
`deep-transcribe models --help` prints the exact current models.

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

- Run `deep-transcribe transcribe --help` before changing transcription options.
- Preserve the workspace after a failure so completed work remains reusable.
- Confirm `ffmpeg` and a JavaScript runtime are on `PATH` when media acquisition fails.
- Confirm required key names exist without echoing their values.
- Use `--json` for machine-readable artifact paths and errors.
- Inspect the workspace log before deciding that a paid stage must be repeated.
- Run `deep-transcribe --skill` when an agent needs the current operational contract.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
