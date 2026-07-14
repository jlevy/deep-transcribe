# deep-transcribe

High-quality transcription, formatting, and analysis of videos and podcasts.

Take a video or audio URL (such as YouTube), download and cache it, and perform a “deep
transcription” of it: full transcription, speaker identification, sections, timestamps,
frame captures, and optional research annotations on key topics.
The level of detail and annotation depends on the options you specify.

It uses [Deepgram](https://deepgram.com/) (the `nova-2` model) for transcription and
diarization and LLMs for analysis and summarization.
By default the LLM steps use
[Claude Sonnet 4.5 and Claude Haiku 4.5](https://docs.claude.com/en/docs/about-claude/models)
and speaker identification uses
[OpenAI gpt-4o-mini](https://platform.openai.com/docs/models); models are configurable
via [kash](https://github.com/jlevy/kash) settings.

This tool is built on kash and its [kash-media](https://github.com/jlevy/kash-media) kit
of tools for handling videos.

## Usage

### Installation

Install with [uv](https://docs.astral.sh/uv/) (Python 3.13 is required and uv will fetch
it automatically):

```bash
uv tool install deep-transcribe
```

You will also need [ffmpeg](https://ffmpeg.org/) installed and on your path for media
handling.

### Key Setup

The default processing needs three API keys: `DEEPGRAM_API_KEY` (transcription),
`ANTHROPIC_API_KEY` (analysis and summarization), and `OPENAI_API_KEY` (speaker
identification). Copy `.env.template` to `~/.env` (or another parent directory of where
you run the tool) and fill in the keys you use.
Other providers listed in the template are optional.

### Basic Usage

```bash
# Annotated transcription (sections, summaries, descriptions, frame captures)
# (This is the default behavior and the same as --annotated)
deep-transcribe https://www.youtube.com/watch?v=VIDEO_ID

# Basic transcription (just text)
deep-transcribe https://www.youtube.com/watch?v=VIDEO_ID --basic

# Formatted transcription (with speakers, paragraphs, timestamps)
deep-transcribe https://www.youtube.com/watch?v=VIDEO_ID --formatted

# Deep processing (everything including research annotations)
deep-transcribe https://www.youtube.com/watch?v=VIDEO_ID --deep

# Custom transcription options
deep-transcribe https://www.youtube.com/watch?v=VIDEO_ID --with format,insert_section_headings,research_paras
```

### Available Options

Use `--help` to see all current options.

The `--with` flag accepts these processing options:

- `format`: Apply the formatting pipeline (speakers, paragraphs, timestamps)

- `identify_speakers`: Identify different speakers in the audio

- `insert_section_headings`: Add section headings to break up content

- `add_summary_bullets`: Add a bulleted summary

- `add_description`: Add a description at the top

- `insert_frame_captures`: Insert frame captures from video

- `research_paras`: Add research annotations to paragraphs

### Presets

- `--basic`: Just transcription (equivalent to no additional options)

- `--formatted`: Transcription plus formatting (equivalent to
  `--with identify_speakers,format`)

- `--annotated`: Full processing except research (equivalent to
  `--with identify_speakers,format,insert_section_headings,add_summary_bullets,add_description,insert_frame_captures`).
  This is the default when no preset is specified.

- `--deep`: Complete processing including research (equivalent to
  `--with identify_speakers,format,insert_section_headings,research_paras,add_summary_bullets,add_description,insert_frame_captures`)

## Output

The tool generates:

- **Markdown file**: Clean, formatted transcript with a few HTML tags for citations

- **HTML file**: Browser-ready version with rich formatting and navigation

- **Cached files**: Original video and audio files and intermediate processing results

All files are stored in the workspace directory (default: `./transcriptions/`). After a
run you can also open the workspace with the `kash` shell to inspect outputs or run
further actions.

## MCP Server

Run as an MCP server for integration with other tools.
The MCP server exposes four transcription actions:

- `transcribe_annotated`: Annotated transcription (recommended default)

- `transcribe_formatted`: Formatted transcription

- `transcribe_basic`: Basic transcription only

- `transcribe_deep`: Complete processing including research

```bash
# Run as stdio MCP server
deep-transcribe --mcp

# Run as SSE MCP server at 127.0.0.1:4440
deep-transcribe --sse

# View MCP server logs
deep-transcribe --logs
```

Both `--sse` and `--logs` imply MCP mode, so you don’t need to specify `--mcp` with
them.

### Claude Desktop Configuration

For Claude Desktop, a config like this works (with the path adjusted to where
`uv tool install` placed the binary, typically `~/.local/bin`):

```json
{
  "mcpServers": {
    "deep_transcribe": {
      "command": "/Users/YOURNAME/.local/bin/deep-transcribe",
      "args": ["--mcp"]
    }
  }
}
```

## Project Docs

For how to install uv and Python, see [installation.md](docs/installation.md).

For development workflows, see [development.md](docs/development.md).

For instructions on publishing to PyPI, see [publishing.md](docs/publishing.md).

* * *

*This project was built from
[simple-modern-uv](https://github.com/jlevy/simple-modern-uv).*

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
