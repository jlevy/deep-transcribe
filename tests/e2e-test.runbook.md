# Deep Transcribe Release Test Runbook

Run this manual, agent-reviewed test before every release. Unit tests verify request
construction; this runbook verifies the real YouTube, Deepgram, LLM, formatting, and
export path and requires a model to review the output quality.

## Release Gate

The release passes only when:

- the source checkout is clean except for the intended release changes;
- `make lint` and `make test` pass;
- a fresh workspace completes the basic and default annotated runs below;
- the log proves Deepgram used `nova-3` with `diarize_model=latest`;
- both the Anthropic and OpenAI model profiles complete the formatted LLM path;
- Markdown and HTML artifacts pass the transcript, speaker, timestamp, annotation, and
  rendering review below.

Do not waive a missing API key, unavailable test video, provider failure, or material
quality regression. Record it as a blocked or failed release test.

## Test Fixture

Use this 1 minute 45 second two-speaker interview:

```text
https://www.youtube.com/watch?v=naIkpQ_cIt0
```

The title is `Job Interview: I Want to Learn (ESL)`. The video has human English
captions and frequent speaker changes, so it gives a compact reference for
transcription, diarization, speaker naming, and timestamp quality. If it becomes
unavailable, replace it in this runbook with another public, captioned, two-speaker
video under three minutes before continuing.

Expected speakers are interviewer Susan Thompson and applicant Mary Hansen.

## Preflight

Run from the repository root with the exact dependency versions intended for release.
Use local editable dependencies when testing unreleased `kash-shell`, `kash-docs`, or
`kash-media` changes.

```shell
uv sync --all-groups
uv run deep-transcribe --version
uv pip show deep-transcribe kash-media kash-docs kash-shell deepgram-sdk litellm
make lint
make test
```

Set `DEEPGRAM_API_KEY`, `ANTHROPIC_API_KEY`, and `OPENAI_API_KEY`. Never print their
values. Confirm they are present:

```shell
for key in DEEPGRAM_API_KEY ANTHROPIC_API_KEY OPENAI_API_KEY; do
    test -n "$(printenv "$key")" || { echo "$key is not set"; exit 1; }
done
```

Create an isolated workspace and retain it until review is complete:

```shell
export DEEP_TRANSCRIBE_E2E_URL='https://www.youtube.com/watch?v=naIkpQ_cIt0'
export DEEP_TRANSCRIBE_E2E_WS="$(mktemp -d)/deep-transcribe-e2e"
echo "$DEEP_TRANSCRIBE_E2E_WS"
```

## Live Transcription and Deterministic Formatting

Run a fresh basic transcription:

```shell
uv run deep-transcribe \
    --workspace "$DEEP_TRANSCRIBE_E2E_WS" \
    --basic \
    --language en \
    "$DEEP_TRANSCRIBE_E2E_URL"
```

Then exercise HTML stripping, paragraph formatting, timestamp backfilling, and HTML
export independently of an LLM:

```shell
uv run deep-transcribe \
    --workspace "$DEEP_TRANSCRIBE_E2E_WS" \
    --basic \
    --with format \
    --rerun \
    --language en \
    "$DEEP_TRANSCRIBE_E2E_URL"
```

Inspect the workspace log. It must contain a successful Deepgram request with these
query parameters and no legacy diarization flag:

```shell
rg -n 'api\.deepgram\.com/v1/listen' "$DEEP_TRANSCRIBE_E2E_WS/logs/workspace.log"
rg -n 'model=nova-3' "$DEEP_TRANSCRIBE_E2E_WS/logs/workspace.log"
rg -n 'diarize_model=latest' "$DEEP_TRANSCRIBE_E2E_WS/logs/workspace.log"
```

## Anthropic Profile

Configure the workspace and run the default annotated pipeline:

```shell
KASH_WS_ROOT="$DEEP_TRANSCRIBE_E2E_WS" uv run kash set_params \
    careful_llm=claude-fable-5 \
    structured_llm=claude-sonnet-5 \
    standard_llm=claude-sonnet-5 \
    fast_llm=claude-haiku-4-5-20251001

uv run deep-transcribe \
    --workspace "$DEEP_TRANSCRIBE_E2E_WS" \
    --annotated \
    --rerun \
    --language en \
    "$DEEP_TRANSCRIBE_E2E_URL"
```

Confirm the log records the configured Anthropic models and contains no provider
authentication, unsupported-model, or malformed-output error.

## OpenAI Profile

Switch the same workspace to the equivalent OpenAI roles and rerun the formatted LLM
path. The media cache prevents another paid transcription request while `--rerun`
forces speaker identification and formatting to execute again.

```shell
KASH_WS_ROOT="$DEEP_TRANSCRIBE_E2E_WS" uv run kash set_params \
    careful_llm=gpt-5.6-sol \
    structured_llm=gpt-5.6-terra \
    standard_llm=gpt-5.6-terra \
    fast_llm=gpt-5.6-luna

uv run deep-transcribe \
    --workspace "$DEEP_TRANSCRIBE_E2E_WS" \
    --formatted \
    --rerun \
    --language en \
    "$DEEP_TRANSCRIBE_E2E_URL"
```

Confirm the log records `gpt-5.6-luna` for speaker identification and contains no
provider authentication, unsupported-model, or malformed-output error.

The optional `--deep` preset also performs paragraph research and may require
additional research-provider credentials. Run it when that integration is part of the
release scope; do not substitute it for the required annotated run.

## Transcript Quality Review

Download the human captions as a temporary reference:

```shell
uv run yt-dlp \
    --skip-download \
    --write-subs \
    --sub-langs en \
    --sub-format vtt \
    -o "$DEEP_TRANSCRIBE_E2E_WS/reference.%(ext)s" \
    "$DEEP_TRANSCRIBE_E2E_URL"
```

Have the reviewing model read the reference captions, raw transcription, final
Markdown, and final HTML. Review at least the beginning, middle, and end against the
video. Do not rely only on file sizes or command exit status.

The transcript passes when:

- all statements are present in the right order with no invented content;
- names, job terms, times, and other meaning-bearing words match the audio;
- punctuation and paragraph boundaries are readable;
- Susan and Mary remain consistently labeled across long turns;
- no paragraph combines a question and answer from different speakers, except a
  genuine overlap or an isolated brief interjection noted in the report;
- every transcript paragraph has a timestamp near its first spoken word, including the
  first and last paragraphs, and sampled links land within about two seconds;
- speaker identification names Susan Thompson and Mary Hansen consistently;
- the annotated output has an accurate description and summary, useful section
  headings, relevant frame captures, and no unsupported claims;
- the HTML renders without raw template syntax, broken links, missing media, clipped
  text, or unreadable styling.

Minor punctuation or filler-word differences may pass when meaning is unchanged. Any
missing phrase, wrong proper noun, mixed-speaker paragraph, shifted timestamp series,
hallucinated summary claim, or repeated processing artifact is a release blocker until
fixed or explicitly accepted by the release owner.

## Report

Record this evidence in the release task or pull request:

```text
Deep Transcribe E2E: PASS | FAIL | BLOCKED
Commit:
Dependency versions:
Tested at:
Video title and duration:
Deepgram request model and diarizer:
Anthropic models observed:
OpenAI models observed:
Raw transcript artifact:
Final Markdown artifact:
Final HTML artifact:
Transcript findings:
Diarization and speaker-name findings:
Timestamp findings:
Annotation and frame-capture findings:
HTML rendering findings:
Material defects or follow-up issues:
Reviewer verdict:
```

Delete the temporary workspace only after the report is complete:

```shell
rm -rf "$DEEP_TRANSCRIBE_E2E_WS"
```
