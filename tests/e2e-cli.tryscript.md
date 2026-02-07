---
env:
  NO_COLOR: "1"
  TEST_WS: ./test-transcriptions
path:
  - ../.venv/bin
---

# deep-transcribe CLI Tests

These tests validate the deep-transcribe CLI. Fast tests (help, version, skill,
error handling) need no API keys. Transcription tests require `DEEPGRAM_API_KEY`
and `ANTHROPIC_API_KEY`.

## Workflow

Run and update golden output:

    npx tryscript@latest run --update tests/e2e-cli.tryscript.md

Then review changes:

    git diff tests/e2e-cli.tryscript.md

If the output looks right, commit it. If not, investigate.

---

## Fast Tests (no API keys needed)

# Test: Help output

```console
$ deep-transcribe --help
Usage: deep-transcribe [..]
...
? 0
```

# Test: Version output

```console
$ deep-transcribe --version
deep-transcribe [..]
? 0
```

# Test: Skill output

```console
$ deep-transcribe --skill
---
name: [..]
...
? 0
```

# Test: Missing URL error

```console
$ deep-transcribe 2>&1
Usage: deep-transcribe [-h] [--version] [--basic] [--formatted] [--annotated]
                       [--deep] [--with WITH_FLAGS] [--no-minify]
                       [--workspace WORKSPACE] [--language LANGUAGE] [--rerun]
                       [--install-skill] [--agent-base DIR] [--skill] [--mcp]
                       [--sse] [--logs]
                       [url]
deep-transcribe: error: URL is required unless --mcp is specified
? 2
```

# Test: Invalid --with flag

```console
$ deep-transcribe --with nonexistent_flag https://example.com 2>&1
...
? 1
```

---

## Transcription Tests (requires API keys and network)

These tests transcribe a real video. They take several minutes each and
cost real API credits. The test video should be short (2-5 min) and have
at least two speakers for speaker identification testing.

Test video (NASA Perseverance Mars landing, ~3 min, public domain):
https://www.youtube.com/watch?v=4czjS9h4Fpg

# Test: Clean workspace <!-- skip -->

```console
$ rm -rf $TEST_WS
? 0
```

# Test: Basic transcription <!-- skip -->

```console
$ deep-transcribe --basic --workspace $TEST_WS https://www.youtube.com/watch?v=4czjS9h4Fpg 2>&1
...
? 0
```

# Test: Basic output file structure <!-- skip -->

```console
$ find $TEST_WS -type f -name "*.md" -o -name "*.html" | sort
...
```

# Test: Basic transcript word count <!-- skip -->

```console
$ find $TEST_WS -name "*.md" -path "*/workspace/*" | head -1 | xargs wc -w
...
```

# Test: Formatted transcription <!-- skip -->

```console
$ deep-transcribe --formatted --workspace $TEST_WS https://www.youtube.com/watch?v=4czjS9h4Fpg 2>&1
...
? 0
```

# Test: Formatted output has speakers <!-- skip -->

```console
$ find $TEST_WS -name "*.md" -path "*/workspace/*" -newer $TEST_WS/workspace | head -1 | xargs grep -c "Speaker" || echo "0 speakers found"
...
```

# Test: Annotated transcription (default) <!-- skip -->

```console
$ deep-transcribe --annotated --workspace $TEST_WS https://www.youtube.com/watch?v=4czjS9h4Fpg 2>&1
...
? 0
```

# Test: Annotated output has section headings <!-- skip -->

```console
$ find $TEST_WS -name "*.md" -path "*/workspace/*" -newer $TEST_WS/workspace | head -1 | xargs grep -c "^##" || echo "0 headings"
...
```

# Test: Annotated HTML output exists <!-- skip -->

```console
$ find $TEST_WS -type f -name "*.html" | wc -l
...
```

# Test: Deep transcription <!-- skip -->

```console
$ deep-transcribe --deep --workspace $TEST_WS https://www.youtube.com/watch?v=4czjS9h4Fpg 2>&1
...
? 0
```

# Test: Workspace summary <!-- skip -->

```console
$ echo "=== Files ===" && find $TEST_WS/workspace -type f | sort && echo "=== Word counts ===" && find $TEST_WS/workspace -name "*.md" -exec sh -c 'echo "$(wc -w < "$1") $1"' _ {} \;
...
```
