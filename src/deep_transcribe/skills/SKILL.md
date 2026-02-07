---
name: deep-transcribe
description: High-quality transcription, formatting, and analysis of videos and podcasts. Use when user wants to transcribe a YouTube video, podcast, or audio/video URL, or when user mentions deep-transcribe.
allowed-tools: Bash(deep-transcribe:*), Bash(uvx deep-transcribe@latest:*), Read, Write
---
# deep-transcribe - Video & Podcast Transcription

> **Full documentation: Run `uvx deep-transcribe@latest --help` for all options.**

High-quality transcription with speaker identification, section headings, summaries,
frame captures, and research annotations. Uses Deepgram for transcription and Claude
for analysis.

## Quick Start

```bash
# Default: annotated transcription (sections, summaries, frame captures)
uvx deep-transcribe@latest https://www.youtube.com/watch?v=VIDEO_ID

# Basic transcription (just text)
uvx deep-transcribe@latest --basic https://www.youtube.com/watch?v=VIDEO_ID

# Deep processing (everything including research annotations)
uvx deep-transcribe@latest --deep https://www.youtube.com/watch?v=VIDEO_ID
```

## When to Use deep-transcribe

**Use deep-transcribe for:**
- Transcribing YouTube videos, podcasts, or any audio/video URL
- Getting formatted transcripts with speaker identification
- Creating annotated transcripts with sections, summaries, and descriptions
- Deep analysis with research annotations on key topics
- Generating both Markdown and HTML versions of transcripts

**Don't use deep-transcribe for:**
- Transcribing local audio files that aren't accessible via URL
- Real-time/live transcription
- Simple text-to-speech or speech synthesis

## Presets

| Preset | What It Does |
| --- | --- |
| `--basic` | Just transcription text |
| `--formatted` | + speaker identification, paragraphs, timestamps |
| `--annotated` | + section headings, summaries, descriptions, frame captures (default) |
| `--deep` | + research annotations on key topics |

## Custom Options

Use `--with` for fine-grained control:

```bash
uvx deep-transcribe@latest --with format,identify_speakers,research_paras https://example.com/video
```

Available options: `identify_speakers`, `format`, `insert_section_headings`,
`research_paras`, `add_summary_bullets`, `add_description`, `insert_frame_captures`

## Key Flags

| Flag | Purpose |
| --- | --- |
| `--basic` | Basic transcription only |
| `--formatted` | Formatted with speakers and timestamps |
| `--annotated` | Full annotations (default) |
| `--deep` | Complete processing with research |
| `--with OPTIONS` | Comma-separated custom options |
| `--workspace DIR` | Output directory (default: `./transcriptions`) |
| `--language CODE` | Language code (default: `en`) |
| `--no-minify` | Skip HTML minification |
| `--mcp` | Run as MCP server (stdio) |
| `--sse` | Run as SSE MCP server |

## Output

Generates two files in the workspace directory:
- **Markdown** (.md) — clean transcript with HTML citation tags
- **HTML** (.html) — browser-ready with rich formatting

## Notes

- Requires `DEEPGRAM_API_KEY` and `ANTHROPIC_API_KEY` environment variables
- Results are cached in the workspace directory for reuse
- The `--annotated` preset is the default and recommended for most use cases
- Frame captures are extracted from video content (not available for audio-only)
