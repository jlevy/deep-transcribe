---
name: deep-transcribe
description: Transcribes and analyzes audio, video, podcasts, and YouTube URLs with Deepgram plus Anthropic or OpenAI models. Use when an agent needs a transcript, speaker labels, timestamps, sections, summaries, research annotations, frame captures, HTML output, or the Deep Transcribe MCP server.
---

# Deep Transcribe

Use Deep Transcribe for complete media transcription and transcript processing. The CLI
is the source of truth for commands, options, models, defaults, and examples.

## Start with CLI Help

First try the local executable:

```shell
deep-transcribe --help
```

If it is unavailable, use the pinned zero-install runner:

```shell
uvx --from deep-transcribe==0.1.9 deep-transcribe --help
```

Use the same executable prefix for later commands. Do not install the package globally
just to use this skill. If both commands fail, stop and report that `uv` or Deep
Transcribe is unavailable.

Run the relevant help command before acting:

- `deep-transcribe transcribe --help` for URLs and local audio or video, processing
  presets, individual stages, source metadata, speaker corrections, Deepgram settings,
  caching, and JSON artifact paths
- `deep-transcribe models --help` to inspect or persist the current Anthropic and OpenAI
  profiles
- `deep-transcribe mcp --help` to expose every transcription preset as an MCP tool
- `deep-transcribe logs --help` to follow MCP server logs

The existing flag-only CLI remains compatible, but prefer the command form because its
help is organized by task.

## Execution

Before transcription, confirm that `ffmpeg` is available and that the environment has
`DEEPGRAM_API_KEY` plus the key for the selected LLM profile:
`ANTHROPIC_API_KEY` or `OPENAI_API_KEY`. Never print secrets or change an existing
workspace model profile unless the user requests it.

Choose the least expensive preset that meets the request. Use custom stages only when
the requested output differs from a preset. Run with JSON output when artifact paths
will be consumed programmatically.

When the user supplies names, terminology, roles, or recording context, follow the
metadata options shown by `transcribe --help`. Prefer a reusable metadata file for
corrections. Rerun with the updated file; semantic corrections reuse the raw transcript,
while key-term changes intentionally request a new transcription. Use the documented
downstream-only rerun flag when forcing formatting or model processing without refreshing
speech-to-text.

After completion, report the workspace, transcript, and HTML paths. When quality review
is requested, inspect the source transcript and rendered HTML for missing speech,
speaker-label errors, timestamp drift, unsupported annotations, and broken frame
captures.
