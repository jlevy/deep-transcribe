# deep-transcribe

Take a video or audio URL (such as YouTube), download and cache it, and perform a "deep
transcription" of it, including full transcription, identifying speakers, adding
sections, timestamps, and annotations, and inserting frame captures.

By default this needs API keys for Deepgram and Anthropic (Claude).

This is built on [kash](https://www.github.com/jlevy/kash) and its
[kash-media](https://www.github.com/jlevy/kash-media) kit of tools for handling videos.

## Usage

See the `env.template` to set up DEEPGRAM_API_KEY and ANTHROPIC_API_KEY.

```shell
uv tool install --upgrade deep_transcribe

# Pick a YouTube video, and do a basic, formatted, or fully annotated transcription:
deep_transcribe transcribe https://www.youtube.com/watch?v=ihaB8AFOhZo
deep_transcribe transcribe_format https://www.youtube.com/watch?v=ihaB8AFOhZo
deep_transcribe transcribe_annotate https://www.youtube.com/watch?v=ihaB8AFOhZo
```

Results will be in the `./transcriptions` directory.

To run as an MCP server:

```shell
# In stdio mode:
deep_transcribe mcp

# In SSE mode at 127.0.0.1:4440:
deep_transcribe mcp --sse
```

Or for Claude Desktop, a config like this should work (adjusted to use your appropriate home folder):

```json
{
  "mcpServers": {
    "deep_transcribe": {
      "command": "/Users/levy/.local/bin/deep-transcribe",
      "args": ["mcp"]
    }
  },
}
```

To debug MCP logs:

```shell
deep_transcribe mcp --logs
```

## Project Docs

For how to install uv and Python, see [installation.md](installation.md).

For development workflows, see [development.md](development.md).

For instructions on publishing to PyPI, see [publishing.md](publishing.md).

* * *

*This project was built from
[simple-modern-uv](https://github.com/jlevy/simple-modern-uv).*
```
```
