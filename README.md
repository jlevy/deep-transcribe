# deep-transcribe

High-quality transcription, formatting, and analysis of videos and podcasts.

Deep Transcribe accepts YouTube and other media URLs or local audio and video files. It
uses Deepgram Nova-3 with the current batch diarizer, then can identify speakers, format
paragraphs and timestamps, add sections and summaries, research key passages, capture
video frames, and export browser-ready HTML.

LLM processing uses configurable [kash](https://github.com/jlevy/kash) model roles. New
workspaces use the current Anthropic profile by default, and an equivalent OpenAI
profile is included.

## Requirements

Install [uv](https://docs.astral.sh/uv/) and
[ffmpeg](https://ffmpeg.org/). Deep Transcribe requires Python 3.13, which uv fetches
automatically.

Set `DEEPGRAM_API_KEY` and one LLM provider key in the process environment or a
`.env` file in the current directory or one of its parents:

- `ANTHROPIC_API_KEY` for the default Anthropic profile
- `OPENAI_API_KEY` for the OpenAI profile

Do not commit API keys.

## Zero-Install CLI

Run the pinned release without installing it globally:

```shell
uvx --from deep-transcribe==0.1.6 deep-transcribe --help
```

For repeated human use, a persistent tool install is also available:

```shell
uv tool install deep-transcribe
deep-transcribe --help
```

## Cross-Agent Skill

Install the repository skill through the cross-agent skills installer:

```shell
npx skills add jlevy/deep-transcribe
```

The skill uses a local `deep-transcribe` executable when available and otherwise uses
the pinned zero-install runner. It routes agents to CLI help rather than carrying a
second copy of the command manual.

## Self-Documenting CLI

Start with the top-level command directory, then open the help page for the relevant
task:

```shell
deep-transcribe --help
deep-transcribe transcribe --help
deep-transcribe models --help
deep-transcribe mcp --help
deep-transcribe logs --help
```

The command pages document all presets, individual processing stages, Deepgram language
selection, caching and rerun behavior, JSON output, model profiles, MCP tools, and
examples. Existing flag-only invocations remain supported for backward compatibility.

### Model Provider

Inspect the exact current Anthropic and OpenAI role mappings before selecting one:

```shell
deep-transcribe models
deep-transcribe models --set anthropic
deep-transcribe models --set openai
```

The selection is saved in the chosen workspace. Pass `--workspace` to `models` and
`transcribe` when using a location other than `./transcriptions`.

### Quick Demo

This short two-person hotel dialogue exercises transcription and diarization:

```shell
deep-transcribe transcribe --basic \
    "https://www.youtube.com/watch?v=wyqfYJX23lg"
```

Use `deep-transcribe transcribe --help` to choose formatted, annotated, deep, or custom
processing.

## Output

Each run reports:

- the workspace containing cached media and intermediate results
- the transcript source
- browser-ready HTML

Use `--json` when another tool or agent needs stable artifact paths. You can also open
the workspace with `kash` to inspect cached and intermediate items.

## MCP Server

Run `deep-transcribe mcp --help` for the available transcription tools and transports.
Run `deep-transcribe logs --help` for server log handling.

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
