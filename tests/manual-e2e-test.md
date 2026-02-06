# Manual E2E Test

Run these tests before each release to verify deep-transcribe works end-to-end.

**Prerequisites:** `DEEPGRAM_API_KEY` and `ANTHROPIC_API_KEY` must be set.

## Test Video

Use a short (2-3 min) public domain video. The NASA "Perseverance Rover's Descent and
Touchdown on Mars" is a good choice (official NASA, public domain):

```
https://www.youtube.com/watch?v=4czjS9h4Fpg
```

Or use any short podcast/interview clip you have access to.

## Test Commands

Run each preset and verify the output:

```bash
# Clean workspace
rm -rf ./test-transcriptions

# 1. Basic transcription
deep-transcribe --workspace ./test-transcriptions --basic https://www.youtube.com/watch?v=4czjS9h4Fpg

# 2. Formatted transcription
deep-transcribe --workspace ./test-transcriptions --formatted https://www.youtube.com/watch?v=4czjS9h4Fpg

# 3. Annotated transcription (default)
deep-transcribe --workspace ./test-transcriptions --annotated https://www.youtube.com/watch?v=4czjS9h4Fpg

# 4. Deep transcription
deep-transcribe --workspace ./test-transcriptions --deep https://www.youtube.com/watch?v=4czjS9h4Fpg

# 5. Custom --with flags
deep-transcribe --workspace ./test-transcriptions --with format,identify_speakers https://www.youtube.com/watch?v=4czjS9h4Fpg
```

## What to Validate

For each run, check:

1. **Exits cleanly** — no Python tracebacks or unhandled errors
2. **Markdown output** — file exists, non-empty, contains transcription text
3. **HTML output** — file exists, non-empty, renders in a browser
4. **For --formatted and above** — speakers identified, paragraphs formatted
5. **For --annotated** — section headings present, summary bullets, description
6. **For --deep** — research annotations present in addition to above
7. **Frame captures** (--annotated, --deep) — image references in markdown/HTML

## MCP Server Test

```bash
# Start MCP server (Ctrl-C to stop)
deep-transcribe --mcp

# Or start SSE server
deep-transcribe --sse
# Then verify it responds at http://127.0.0.1:4440
```

## Cleanup

```bash
rm -rf ./test-transcriptions
```
