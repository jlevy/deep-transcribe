# deep-transcribe

High-quality transcription, formatting, and analysis of videos and podcasts.

It currently uses [Deepgram](https://deepgram.com/) for transcription and diarization
and [Claude Sonnet 4](https://docs.anthropic.com/en/docs/about-claude/models/overview)
or [OpenAI o3](https://platform.openai.com/docs/models) for analysis and summarization.

Take a video or audio URL (such as YouTube), download it, and perform a “deep
transcription” of it, including full transcription, identifying speakers, adding
sections, timestamps, inserting frame captures, and researching or footnoting key
topics.

What kind of detail and annotations it includes depends on the options you specify.

By default this needs API keys for Deepgram and Anthropic (Claude).

This is built on [kash](https://www.github.com/jlevy/kash) and its
[kash-media](https://www.github.com/jlevy/kash-media) kit of tools for handling videos.

## Usage

### Key Setup

See the `env.template` to set up DEEPGRAM_API_KEY and ANTHROPIC_API_KEY.

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

- `format`: Apply formatting pipeline (speakers, paragraphs, timestamps)

- `identify_speakers`: Identify different speakers in the audio

- `insert_section_headings`: Add section headings to break up content

- `add_summary_bullets`: Add a bulleted summary

- `add_description`: Add a description at the top

- `insert_frame_captures`: Insert frame captures from video

- `research_paras`: Add research annotations to paragraphs

### Presets

- `--basic`: Just transcription (equivalent to no additional options)

- `--formatted`: Transcription + formatting (equivalent to `--with
  identify_speakers,format`)

- `--annotated`: Full processing except research (equivalent to `--with
  identify_speakers,format,insert_section_headings,add_summary_bullets,add_description,insert_frame_captures`)
  \- **default when no preset specified**

- `--deep`: Complete processing including research (equivalent to `--with
  identify_speakers,format,insert_section_headings,research_paras,add_summary_bullets,add_description,insert_frame_captures`)

## Output

The tool generates:
- **Markdown file**: Clean, formatted transcript with HTML tags for citations

- **HTML file**: Browser-ready version with rich formatting and navigation

- **Cached files**: Original video/audio files and intermediate processing results

All files are stored in the workspace directory (default: `./transcriptions/`).

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

Note: Both `--sse` and `--logs` automatically enable MCP mode, so you don’t need to
specify `--mcp` explicitly.

### Claude Desktop Configuration

For Claude Desktop, a config like this should work (adjusted to use your appropriate
home folder):

```json
{
  "mcpServers": {
    "deep_transcribe": {
      "command": "/Users/levy/.local/bin/deep-transcribe",
      "args": ["--mcp"]
    }
  }
}
```

## Project Docs

For how to install uv and Python, see [installation.md](installation.md).

For development workflows, see [development.md](development.md).

For instructions on publishing to PyPI, see [publishing.md](publishing.md).

* * *

*This project was built from
[simple-modern-uv](https://github.com/jlevy/simple-modern-uv).*
