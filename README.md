# deep-transcribe

High-quality transcription, formatting, and analysis of videos and podcasts.

Deep Transcribe accepts YouTube and other media URLs or local audio and video files.
It uses Deepgram Nova-3 with the current batch diarizer, then can identify speakers,
format paragraphs and timestamps, add sections and summaries, research key passages,
capture video frames, and export browser-ready HTML.

LLM processing uses configurable [kash](https://github.com/jlevy/kash) model roles.
New workspaces use the current Anthropic profile by default, and an equivalent OpenAI
profile is included.

## Requirements

Install [uv](https://docs.astral.sh/uv/) and [ffmpeg](https://ffmpeg.org/). Deep
Transcribe requires Python 3.13, which uv fetches automatically.

For YouTube sources, also install a JavaScript runtime — [deno](https://deno.com/)
(preferred), or Node.js or bun if you already have one.
yt-dlp uses it to solve the JavaScript challenges YouTube now applies to media URLs.
Audio-only transcription generally still works without a runtime, but yt-dlp warns on
every fetch and loses access to some formats, so treat it as required in practice.
Environments without a system runtime (containers, bare CI) can install the
redistributed binary instead, with `uv pip install deno`.

Set `DEEPGRAM_API_KEY` and one LLM provider key in the process environment, a `.env` or
`.env.local` file in the current directory or one of its parents, or `~/.env.local`:

- `ANTHROPIC_API_KEY` for the default Anthropic profile
- `OPENAI_API_KEY` for the OpenAI profile

Do not commit API keys.

## Zero-Install CLI

Run the pinned release without installing it globally:

```shell
uvx \
    --exclude-newer-package yt-dlp=2026-08-20T00:00:00Z \
    --from deep-transcribe==0.1.11 \
    deep-transcribe --help
```

The yt-dlp cutoff carries this release’s reviewed freshness exception through uv
installations that enforce a global dependency cool-off.

For repeated human use, a persistent tool install is also available:

```shell
uv tool install deep-transcribe
deep-transcribe --help
```

## Cross-Agent Skill

Install the public discovery skill through the cross-agent skills installer:

```shell
npx skills add jlevy/deep-transcribe@deep-transcribe
```

The skill uses a local `deep-transcribe` executable when available and otherwise uses
the pinned zero-install runner.
It routes agents to executable documentation rather than carrying a second command
manual.

If the CLI is already available, install its complete skill bundle directly from a
project root:

```shell
deep-transcribe --install-skill
```

This writes the portable `.agents/skills/deep-transcribe/` bundle, the
`.claude/skills/deep-transcribe/` mirror, and a marker-bounded project instruction block
in `AGENTS.md`. The install is idempotent.
Run `deep-transcribe --docs` for surface selection and explicit global-install options.

## Self-Documenting CLI

Start with the top-level command directory, then open the help page for the relevant
task:

```shell
deep-transcribe --help
deep-transcribe --docs
deep-transcribe --skill
deep-transcribe transcribe --help
deep-transcribe models --help
```

The command pages document all presets, individual processing stages, Deepgram language
and model selection, source metadata and speaker hints, caching and rerun behavior, JSON
output, model profiles, and examples.
`--docs` prints the complete guide packaged with the installed release, including the
review-and-rerun workflow and skill installation.
Both `deep-transcribe transcribe OPTIONS INPUT` and the concise
`deep-transcribe OPTIONS INPUT` form are supported transcription interfaces.

### Model Provider

Inspect the exact current Anthropic and OpenAI role mappings before selecting one:

```shell
deep-transcribe models
deep-transcribe models --set anthropic
deep-transcribe models --set openai
```

The selection is saved in the chosen workspace.
Pass `--workspace` to `models` and `transcribe` when using a location other than
`./transcriptions`.

### End-to-End Example: A Reservation Glitch and a Free Jacuzzi

The release test uses a short, two-person
[hotel check-in video](https://www.youtube.com/watch?v=wyqfYJX23lg). Guest Tom Sanders
arrives at the Transnational Hotel, where his reservation briefly goes missing.
The receptionist eventually finds it and offers him a free business-suite upgrade with a
Jacuzzi.
It is about 2 minutes 40 seconds long, has two clearly alternating speakers, and
includes enough names, numbers, and plot details to expose weak transcription or
summarization.

Create a metadata file with information that is known before transcription:

```shell
mkdir hotel-transcript
cd hotel-transcript

cat >hotel.yml <<'YAML'
title: Hotel check-in dialogue
description: A receptionist checks guest Tom Sanders into the Transnational Hotel.
additional_context: |
  This is a two-person hotel check-in conversation. Speaker 0 is the Hotel Receptionist.
  Speaker 1 is guest Tom Sanders, who has a three-night reservation and is assigned
  Room 653.
key_terms:
  - Tom Sanders
  - Transnational Hotel
  - Room 653
speaker_hints:
  "0": Hotel Receptionist
  "1": Tom Sanders
YAML
```

Run the annotated workflow:

```shell
deep-transcribe transcribe \
    --workspace ./output \
    --annotated \
    --language en \
    --metadata ./hotel.yml \
    "https://www.youtube.com/watch?v=wyqfYJX23lg"
```

This one command:

1. downloads and caches the video;
2. transcribes it with Deepgram Nova-3 and the current diarizer, using the key terms;
3. saves the descriptive context and speaker hints with the source item;
4. identifies speakers, formats paragraphs and timestamps, and adds headings, a summary,
   and a description using that context; and
5. captures distinct video frames and exports browser-ready HTML.

The command prints the final Markdown and HTML paths.
In the `v0.1.8` release test, the transcript contained 550 words in 29 speaker turns and
the HTML included 19 distinct frame captures.
Manual review confirmed the two speaker names, Transnational Hotel, Room 653, the
missing reservation, the free suite upgrade, and the check-in instructions.

#### Correct Context Without Paying for Transcription Again

If a speaker name or descriptive detail is wrong, edit `hotel.yml` and rerun only the
semantic processing stages:

```shell
deep-transcribe transcribe \
    --workspace ./output \
    --annotated \
    --metadata ./hotel.yml \
    "https://www.youtube.com/watch?v=wyqfYJX23lg"
```

Changes to `additional_context`, `description`, `speaker_hints`, or `speaker_roster`
change the semantic action inputs.
The normal rerun resumes at the first affected stage, reuses the cached raw Deepgram
transcript and unchanged intermediates, and rebuilds dependent outputs.
If the diarizer merges or splits voices incorrectly, provide the complete
`speaker_roster` and describe roles or dialogue transitions in `additional_context`.
Deep Transcribe then corrects each turn with the careful model profile.
A `key_terms` change intentionally creates a new transcript because it can affect speech
recognition. Full `--rerun` also requests fresh speech-to-text.
Use `--rerun-processing` only when every downstream stage should run again, such as
after changing the saved model profile or when deliberately regenerating model output.

New processing features also reuse earlier work.
For example, add researched paragraph annotations to the existing transcript with
`--with research_paras`; Deep Transcribe reuses compatible formatting and runs that
feature plus the stages that depend on its output.

To compare providers on the same transcript, select the OpenAI profile and rerun the
processing stages:

```shell
deep-transcribe models --workspace ./output --set openai
deep-transcribe transcribe \
    --workspace ./output \
    --annotated \
    --rerun-processing \
    --metadata ./hotel.yml \
    "https://www.youtube.com/watch?v=wyqfYJX23lg"
```

Use `--set anthropic` to switch back.
The same workflow works for a raw `.mp3` or `.mp4`: replace the URL with the local path,
where the metadata is especially useful because a raw file may have no title,
description, speaker names, or other source context.
Run `deep-transcribe transcribe --help` for individual flags and custom processing
stages.

## Output

Each run reports:

- the workspace containing cached media and intermediate results
- the transcript source
- browser-ready HTML

Use `--json` when another tool or agent needs stable artifact paths.
You can also open the workspace with `kash` to inspect cached and intermediate items.

## Built-in Guide

Run `deep-transcribe --docs` for the complete operational guide.
It includes environment setup, context metadata, speaker correction, incremental reruns,
cache verification, model-profile comparisons, output review, privacy, troubleshooting,
and agent-skill installation.
Because the guide ships inside the package, agents can read documentation that matches
the executable they are about to use.

## Project Docs

For environment setup, see [installation.md](docs/installation.md).

For development workflows, see [development.md](docs/development.md).

For the manual, agent-reviewed release test, see
[e2e-test.runbook.md](tests/e2e-test.runbook.md).

For publishing, see [publishing.md](docs/publishing.md).

* * *

*This project was built from
[simple-modern-uv](https://github.com/jlevy/simple-modern-uv).*

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
