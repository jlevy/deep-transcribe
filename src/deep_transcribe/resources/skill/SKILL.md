---
name: deep-transcribe
description: Transcribe and analyze audio, video, podcasts, and YouTube URLs with Deepgram plus Anthropic or OpenAI models. Use for transcripts, speaker labels, timestamps, sections, summaries, research annotations, frame captures, HTML output, or a reviewed result that should be rerun with added context or processing while reusing cached work.
---
# Deep Transcribe

Use Deep Transcribe for media transcription, structured processing, output review, and
cache-aware iteration.
The installed CLI is the source of truth.

## Choose the Runner

In a Deep Transcribe source checkout, prefer the repository environment:

```shell
uv run deep-transcribe --docs
```

This prevents an unrelated or older executable on `PATH` from overriding the checkout.

Outside a source checkout, probe the installed command with `deep-transcribe --docs`.
Use it only when that command succeeds.
A command merely existing on `PATH` is not sufficient because a stale release may have
an incompatible CLI.

If the installed command is missing or rejects `--docs`, use this exact version-pinned
runner:

```shell
uvx \
    --exclude-newer-package yt-dlp=__YTDLP_CUTOFF__ \
    --from "deep-transcribe[youtube]==__DEEP_TRANSCRIBE_VERSION__" \
    deep-transcribe --docs
```

Use the chosen prefix for every later command.
Never substitute `@latest` or an unconstrained package version in an agent workflow.
The per-package cutoff carries Deep Transcribe’s reviewed yt-dlp freshness exception
through uv installations that enforce a global dependency cool-off.
If neither command works, stop and report the missing executable or `uv` prerequisite.

## Read the Executable Documentation

Before acting, run:

- `deep-transcribe --docs` for setup, presets, metadata, iterative reruns, cache reuse,
  output review, privacy, troubleshooting, and skill installation;
- `deep-transcribe --help` for every current transcription option and stage; and
- `deep-transcribe --models` for Anthropic and OpenAI model profiles.

If this skill came from `deep-transcribe --skill`, materialize the complete bundle from
the project root by running `deep-transcribe --install-skill` with the chosen prefix.

## Execute Safely

Confirm `ffmpeg`, `DEEPGRAM_API_KEY`, and the key for the selected LLM profile are
available. Verify key names without printing values.
The `youtube` extra supplies the Deno runtime yt-dlp needs for YouTube sources, so no
system JavaScript runtime is required.
Do not change a workspace’s saved model profile unless the user requests it.

Choose the least expensive preset that meets the request and use `--json` when artifact
paths will be consumed programmatically.
When names, roles, terminology, or chronology are known, supply them with a private
metadata file or the context flags documented by `deep-transcribe --help`. Put
output-shape, emphasis, and level-of-detail requests in `processing_instructions`,
`--instructions`, or `--instructions-file`. If the prose clearly names every speaking
role, Deep Transcribe can derive the internal roster needed to correct merged
diarization boundaries.
Use exact speaker overrides only after reviewing the result.
Do not guess unsupported names.

## Iterate on a Reviewed Result

After each run, read `--report` (add `--json` to get it as data) before opening the page;
it names the headings, themes, segments, speakers, frames, and spelling variants an
agent needs to choose the next correction. Keep a source's recipe in one directory
(`--metadata` file, `--segments` file, README with the command), as
`docs/examples/lex-501/` does, and rebuild the page alone with `--export-only`. View
settings such as `--grouping on|off|MINUTES` (whether the outline, concepts, claims,
and graph group by theme; automatic from 45 minutes) take effect on a re-export, so
change them and re-export rather than rerun. When the
user is going to click through the page, add `--open`: it serves the export locally and
opens it in the browser, which the embedded video player needs and a `file://` URL cannot
give it.

Preserve the exact source and workspace.
Inspect the current transcript and HTML, update the private metadata or add requested
processing instructions or stages, then run the same command normally.
That normal rerun resumes at the first affected action and reuses compatible media,
speech-to-text, and model output.

Use `--rerun-processing` only for a deliberate regeneration of every post-transcription
stage, such as a model-profile comparison.
Use `--rerun` only when a new paid speech-to-text request is wanted.
Changing key terms, language, transcription model, or diarization model intentionally
creates a new transcript cache entry.

For a semantic-only correction, verify from the workspace log that the Deepgram request
count did not increase.
Review speaker continuity and output quality at the beginning, middle, and end; a zero
exit status is not a quality review.

Keep source-specific names, paths, transcript content, metadata, and credentials out of
repository code, tests, docs, commits, pull requests, and issue records.

After completion, report the workspace, transcript, and HTML paths.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
