# Deep Transcribe Release Test Runbook

Run this manual, agent-reviewed test before every release. Unit tests verify request
construction; this runbook verifies the real YouTube, Deepgram, LLM, formatting, and
export path and requires a model to review the output quality.

## Release Gate

The release passes only when:

- the source checkout is clean except for the intended release changes;
- `make lint` and `make test` pass;
- warmed `--help` startup remains below 250 ms and does not import the runtime stack;
- the environment excludes optional document/AWS runtimes and Torch;
- a fresh workspace completes the basic and annotated runs below;
- the log proves Deepgram used `nova-3` with `diarize_model=latest`;
- a raw-file run preserves YAML context, applies explicit speaker corrections, and reuses
  Deepgram unless key terms change;
- the careful-role smoke checks and both provider profiles exercise all six configured
  LLM models successfully;
- Markdown and HTML artifacts pass the transcript, speaker, timestamp, annotation, and
  rendering review below.

Do not waive a missing API key, unavailable test video, provider failure, or material
quality regression. Record it as a blocked or failed release test.

## Test Fixture

Use this 2 minute 40 second two-speaker hotel dialogue:

```text
https://www.youtube.com/watch?v=wyqfYJX23lg
```

The title begins `English for Hotel and Tourism: "Checking into a hotel"`. The video
has clear English audio, two alternating speakers, an explicit guest name, room number,
hotel terminology, and YouTube auto captions. It provides compact coverage of
transcription, diarization, role naming, timestamps, summaries, and frame captures. The
audio is authoritative; auto captions are only a navigation and comparison aid.

Expected labels are `Hotel Receptionist` and `Tom Sanders`. If the video becomes
unavailable, replace it in this runbook with another public, captioned, two-speaker
video under three minutes before continuing.

## Preflight

Run from the repository root with the exact dependency versions intended for release.
Use local editable dependencies when testing unreleased `kash-shell`, `kash-docs`, or
`kash-media` changes.

```shell
uv lock --check
uv sync --locked --all-groups
uv run --locked deep-transcribe --version
uv run --locked deep-transcribe --help
uv run --locked deep-transcribe transcribe --help
uv run --locked deep-transcribe models --help
uv pip show deep-transcribe kash-media kash-docs kash-shell deepgram-sdk litellm
make lint
make test
```

Check the warmed CLI path three times. Each `real` result should remain below 0.25
seconds on a typical development machine:

```shell
for run in 1 2 3; do
    /usr/bin/time -p .venv/bin/deep-transcribe --help >/dev/null
done
```

Measure the installed executable rather than `uv run`; dependency resolution overhead is
not CLI startup time.

Deep Transcribe retains OpenCV and scikit-image for frame capture and visual
deduplication. It must not install unrelated document conversion, AWS, or Torch
runtimes:

```shell
if uv pip list | rg '^(boto3|magika|markitdown|onnxruntime|torch|weasyprint)\b'; then
    echo "Unexpected optional runtime in Deep Transcribe environment"
    exit 1
fi
```

Set `DEEPGRAM_API_KEY`, `ANTHROPIC_API_KEY`, and `OPENAI_API_KEY` in a `.env` file that
kash loads or in the process environment. Never print their values. Confirm that kash
can load them:

```shell
uv run --locked python - <<'PY'
import os

from kash.run import kash_init

kash_init()
required = ("DEEPGRAM_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY")
missing = [name for name in required if not os.getenv(name)]
if missing:
    raise SystemExit(f"Missing API keys: {', '.join(missing)}")
print("Required API keys are available")
PY
```

Create an isolated workspace and retain it until review is complete:

```shell
export DEEP_TRANSCRIBE_E2E_URL='https://www.youtube.com/watch?v=wyqfYJX23lg'
export DEEP_TRANSCRIBE_E2E_WS="$(mktemp -d)/deep-transcribe-e2e"
echo "$DEEP_TRANSCRIBE_E2E_WS"
```

## Live Transcription and Deterministic Formatting

Run a fresh basic transcription:

```shell
uv run --locked deep-transcribe transcribe \
    --workspace "$DEEP_TRANSCRIBE_E2E_WS" \
    --basic \
    --language en \
    "$DEEP_TRANSCRIBE_E2E_URL"
```

Then exercise HTML stripping, paragraph formatting, timestamp backfilling, and HTML
export independently of an LLM:

```shell
uv run --locked deep-transcribe transcribe \
    --workspace "$DEEP_TRANSCRIBE_E2E_WS" \
    --basic \
    --with format \
    --rerun-processing \
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

## Raw File Metadata and Correction Rerun

Download the same fixture as a raw media file and supply metadata that cannot come from
the file itself:

```shell
mkdir -p "$DEEP_TRANSCRIBE_E2E_WS/fixture"
uv run --locked yt-dlp \
    --extract-audio \
    --audio-format mp3 \
    --output "$DEEP_TRANSCRIBE_E2E_WS/fixture/hotel.%(ext)s" \
    "$DEEP_TRANSCRIBE_E2E_URL"

cat >"$DEEP_TRANSCRIBE_E2E_WS/fixture/hotel.yml" <<'YAML'
title: Hotel check-in dialogue
description: A receptionist checks Tom Sanders into a hotel.
additional_context: |
  The two roles are Hotel Receptionist and guest Tom Sanders. Review names and room
  details carefully.
key_terms:
  - Tom Sanders
  - Hotel Receptionist
YAML

uv run --locked deep-transcribe transcribe \
    --workspace "$DEEP_TRANSCRIBE_E2E_WS" \
    --formatted \
    --metadata "$DEEP_TRANSCRIBE_E2E_WS/fixture/hotel.yml" \
    "$DEEP_TRANSCRIBE_E2E_WS/fixture/hotel.mp3"
```

Inspect the raw transcript to determine which Deepgram speaker ID is the receptionist and
which is Tom. Add an authoritative `speaker_hints` mapping to `hotel.yml`; for example,
use the following mapping only if it matches the raw transcript:

```yaml
speaker_hints:
  "0": Hotel Receptionist
  "1": Tom Sanders
```

If Deepgram merged distinct voices under one ID, use a complete roster instead of treating
that ID as authoritative. Describe chronology, forms of address, or exact dialogue transitions
in `additional_context`, then rerun processing:

```yaml
speaker_roster:
  - Hotel Receptionist
  - Tom Sanders
```

The corrected intermediate transcript must use every roster label, preserve every timestamped
ASR span verbatim, and contain no `UNKNOWN` speaker. Review short greetings, interjections, and
sentence fragments at each speaker boundary.

Count Deepgram calls, then rerun the annotated pipeline with the corrected metadata. A
speaker-only or descriptive-context correction must not make another Deepgram request:

```shell
DEEPGRAM_COUNT_BEFORE="$(rg -c 'Transcribing via Deepgram' \
    "$DEEP_TRANSCRIBE_E2E_WS/logs/workspace.log")"

uv run --locked deep-transcribe transcribe \
    --workspace "$DEEP_TRANSCRIBE_E2E_WS" \
    --annotated \
    --rerun-processing \
    --metadata "$DEEP_TRANSCRIBE_E2E_WS/fixture/hotel.yml" \
    "$DEEP_TRANSCRIBE_E2E_WS/fixture/hotel.mp3"

test "$(rg -c 'Transcribing via Deepgram' \
    "$DEEP_TRANSCRIBE_E2E_WS/logs/workspace.log")" = "$DEEPGRAM_COUNT_BEFORE"

test "$(find "$DEEP_TRANSCRIBE_E2E_WS/workspace/resources" \
    -maxdepth 1 -name '*.mp3' | wc -l | tr -d ' ')" = 1
```

Finally add a real phrase from the audio, such as `checking into a hotel`, to `key_terms`
and run `--basic` again. This accuracy-affecting change must make exactly one new Deepgram
request:

```shell
uv run --locked deep-transcribe transcribe \
    --workspace "$DEEP_TRANSCRIBE_E2E_WS" \
    --basic \
    --metadata "$DEEP_TRANSCRIBE_E2E_WS/fixture/hotel.yml" \
    "$DEEP_TRANSCRIBE_E2E_WS/fixture/hotel.mp3"

test "$(rg -c 'Transcribing via Deepgram' \
    "$DEEP_TRANSCRIBE_E2E_WS/logs/workspace.log")" = "$((DEEPGRAM_COUNT_BEFORE + 1))"
```

Confirm the raw-file metadata is present in the source sidematter and propagated into the
final transcript frontmatter. Confirm the correction is reflected in speaker names,
description, summary, and headings without adding unsupported details.

## Local MP4 Frame-Capture Regression

Download the fixture as an MP4 outside a fresh workspace. Run Deep Transcribe from the
repository root, not the fixture directory, so a basename-only lookup cannot accidentally
find the source file in the process working directory:

```shell
LOCAL_VIDEO_WS="$DEEP_TRANSCRIBE_E2E_WS/local-video"

uv run --locked yt-dlp \
    --format 'bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]' \
    --merge-output-format mp4 \
    --output "$DEEP_TRANSCRIBE_E2E_WS/fixture/hotel.mp4" \
    "$DEEP_TRANSCRIBE_E2E_URL"

test "$PWD" != "$DEEP_TRANSCRIBE_E2E_WS/fixture"

uv run --locked deep-transcribe transcribe \
    --workspace "$LOCAL_VIDEO_WS" \
    --annotated \
    --metadata "$DEEP_TRANSCRIBE_E2E_WS/fixture/hotel.yml" \
    "$DEEP_TRANSCRIBE_E2E_WS/fixture/hotel.mp4"

test -n "$(find "$LOCAL_VIDEO_WS/workspace/docs" -type f \
    \( -name '*.jpg' -o -name '*.png' \) -print -quit)"
```

Confirm the run reaches `insert_frame_captures`, resolves the imported resource through
its workspace path, and finishes without `Original filename not found` or `Workspace
resource not found`. Open the exported HTML and verify the local MP4 frame captures load.

## Careful-Role Model Checks

The annotated pipeline exercises the fast and standard roles. Check both configured
careful models directly so every model in the two profiles is live-tested:

```shell
uv run --locked python - <<'PY'
from kash.llm_utils import LLMName, llm_completion
from kash.run import kash_init

kash_init()
for model in ("claude-fable-5", "gpt-5.6-sol"):
    result = llm_completion(
        LLMName(model),
        messages=[{"role": "user", "content": "Reply with exactly OK."}],
    )
    if result.content.strip() != "OK":
        raise SystemExit(f"Unexpected response from {model}")
    print(f"{model}: OK")
PY
```

## Anthropic Profile

Configure the workspace and run the default annotated pipeline:

```shell
uv run --locked deep-transcribe models \
    --workspace "$DEEP_TRANSCRIBE_E2E_WS" \
    --set anthropic

uv run --locked deep-transcribe transcribe \
    --workspace "$DEEP_TRANSCRIBE_E2E_WS" \
    --annotated \
    --rerun-processing \
    --language en \
    "$DEEP_TRANSCRIBE_E2E_URL"
```

Confirm the log records `claude-haiku-4-5-20251001` for speaker identification and
formatting and `claude-sonnet-5` for summaries and descriptions. It must contain no
provider authentication, unsupported-model, or malformed-output error.

## OpenAI Profile

Switch the same workspace to the equivalent OpenAI roles and rerun the annotated path.
The raw transcript cache prevents another paid transcription request while
`--rerun-processing` forces speaker identification, formatting, annotation, and export
to execute again. Reserve `--rerun` for an intentional fresh Deepgram request.

```shell
uv run --locked deep-transcribe models \
    --workspace "$DEEP_TRANSCRIBE_E2E_WS" \
    --set openai

uv run --locked deep-transcribe transcribe \
    --workspace "$DEEP_TRANSCRIBE_E2E_WS" \
    --annotated \
    --rerun-processing \
    --language en \
    "$DEEP_TRANSCRIBE_E2E_URL"
```

Confirm the log records `gpt-5.6-luna` for speaker identification and formatting and
`gpt-5.6-terra` for summaries and descriptions. It must contain no provider
authentication, unsupported-model, or malformed-output error.

The optional `--deep` preset also performs paragraph research and may require
additional research-provider credentials. Run it when that integration is part of the
release scope; do not substitute it for the required annotated run.

## Transcript Quality Review

Download the auto captions as a temporary reference:

```shell
uv run --locked yt-dlp \
    --skip-download \
    --write-auto-subs \
    --sub-langs en-orig \
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
- the receptionist and Tom remain consistently labeled across long turns;
- no paragraph combines a question and answer from different speakers, except a
  genuine overlap or an isolated brief interjection noted in the report;
- every transcript paragraph has a timestamp near its first spoken word, including the
  first and last paragraphs, and sampled links land within about two seconds;
- speaker identification consistently uses `Hotel Receptionist` and `Tom Sanders`;
- the annotated output has an accurate description and summary, useful section
  headings, relevant frame captures, and no unsupported claims;
- every exported frame asset is referenced by the HTML, with no rejected similarity-filter
  candidates left in the export directory;
- the HTML renders without raw template syntax, broken links, missing media, clipped
  text, or unreadable styling.

Serve the workspace locally and have the reviewing agent open each provider's final
HTML export in a browser:

```shell
uv run --locked python -m http.server 8765 \
    --bind 127.0.0.1 \
    --directory "$DEEP_TRANSCRIBE_E2E_WS/workspace"
```

Visually inspect the beginning, middle, and end. Also inspect the rendered DOM and
confirm that every frame image is complete with nonzero natural dimensions, the page
has no horizontal overflow, and no template markers such as `{{` or `}}` are visible.
Broken or missing frame captures fail the release gate.

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
Metadata correction and cache findings:
Reviewer verdict:
```

Delete the temporary workspace only after the report is complete:

```shell
rm -rf "$DEEP_TRANSCRIBE_E2E_WS"
```
