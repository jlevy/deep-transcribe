# Deep Transcribe Release Test Runbook

Run this manual, agent-reviewed test before every release.
Unit tests verify request construction; this runbook verifies the real YouTube,
Deepgram, LLM, formatting, and export path and requires a model to review the output
quality.

## Release Gate

The release passes only when:

- the source checkout is clean except for the intended release changes;
- `make lint` and `make test` pass;
- warmed `--help` startup remains below 250 ms and does not import the runtime stack;
- the environment excludes optional document/AWS runtimes and Torch;
- a fresh workspace completes the basic and annotated runs below;
- a supported URL resource records yt-dlp metadata before transcription;
- the log proves Deepgram used `nova-3` with `diarize_model=latest`;
- a raw-file run preserves recording context, corrects a five-role speaker roster, and
  reuses Deepgram unless recognition inputs change;
- the careful-role smoke checks and both provider profiles exercise all six configured
  LLM models successfully;
- Markdown and HTML artifacts pass the transcript, speaker, timestamp, annotation, and
  rendering review below.

Do not waive a missing API key, unavailable test video, provider failure, or material
quality regression. Record it as a blocked or failed release test.

## Test Fixture

Use this 4 minute 13 second Saturday Night Live sketch:

```text
https://www.youtube.com/watch?v=kq9Q9-U0vrc
```

The official title is `Hotel Check In - SNL`. The video has clear English audio, five
speaking roles, short interjections, an explicit guest name and room number, repeated
hotel terminology, and scene changes.
It provides compact coverage of transcription, multi-speaker diarization, prose-based
role naming and boundary repair, timestamps, summaries, outlines, and frame captures.
The audio is authoritative; auto captions are only a navigation and comparison aid.

Expected labels are `Mr. Adams`, `Front Desk Employee`, `Government Representative`,
`Room 904 Guest (Chris Redd)`, and `Room 904 Guest (Leslie Jones)`. If the video becomes
unavailable, replace it in this runbook with another public, captioned, short video that
has at least three distinct speaking roles before continuing.

## Preflight

Run from the repository root with the exact dependency versions intended for release.
Use local editable dependencies when testing unreleased `kash-shell`, `kash-docs`, or
`kash-media` changes.

```shell
uv lock --check
uv sync --locked --all-groups
uv run --locked deep-transcribe --version
uv run --locked deep-transcribe --help
uv run --locked deep-transcribe --models
uv pip show deep-transcribe kash-media kash-docs kash-shell deepgram-sdk litellm
make lint
make test
```

Check the warmed CLI path three times.
Each `real` result should remain below 0.25 seconds on a typical development machine:

```shell
for run in 1 2 3; do
    /usr/bin/time -p .venv/bin/deep-transcribe --help >/dev/null
done
```

Measure the installed executable rather than `uv run`; dependency resolution overhead is
not CLI startup time.

Deep Transcribe retains OpenCV and scikit-image for frame capture and visual
deduplication.
It must not install unrelated document conversion, AWS, or Torch runtimes:

```shell
if uv pip list | rg '^(boto3|magika|markitdown|onnxruntime|torch|weasyprint)\b'; then
    echo "Unexpected optional runtime in Deep Transcribe environment"
    exit 1
fi
```

Set `DEEPGRAM_API_KEY`, `ANTHROPIC_API_KEY`, and `OPENAI_API_KEY` in a `.env` file that
kash loads or in the process environment.
Never print their values.
Confirm that kash can load them:

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
export DEEP_TRANSCRIBE_E2E_URL='https://www.youtube.com/watch?v=kq9Q9-U0vrc'
export DEEP_TRANSCRIBE_E2E_WS="$(mktemp -d)/deep-transcribe-e2e"
echo "$DEEP_TRANSCRIBE_E2E_WS"
```

## Live Transcription and Deterministic Formatting

Run a fresh basic transcription:

```shell
uv run --locked deep-transcribe \
    --workspace "$DEEP_TRANSCRIBE_E2E_WS" \
    --basic \
    --language en \
    "$DEEP_TRANSCRIBE_E2E_URL"
```

Then exercise HTML stripping, paragraph formatting, timestamp backfilling, and HTML
export independently of an LLM:

```shell
uv run --locked deep-transcribe \
    --workspace "$DEEP_TRANSCRIBE_E2E_WS" \
    --basic \
    --with format \
    --rerun-processing \
    --language en \
    "$DEEP_TRANSCRIBE_E2E_URL"
```

Inspect the saved URL resource.
It must contain the yt-dlp title and description plus the `media_service`,
`upload_date`, `channel_url`, and `duration` fields used as bounded semantic context:

```shell
rg -n '^(title|description):|^  (media_service|upload_date|channel_url|duration):' \
    "$DEEP_TRANSCRIBE_E2E_WS/workspace/resources"
```

Inspect the workspace log.
It must contain a successful Deepgram request with these query parameters and no legacy
diarization flag:

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
    --output "$DEEP_TRANSCRIBE_E2E_WS/fixture/snl-hotel.%(ext)s" \
    "$DEEP_TRANSCRIBE_E2E_URL"

cat >"$DEEP_TRANSCRIBE_E2E_WS/fixture/snl-hotel.yml" <<'YAML'
title: Hotel Check In — SNL
description: An SNL sketch about an increasingly frustrating hotel check-in.
additional_context: |
  This is the Saturday Night Live sketch Hotel Check In. There are five speaking roles:
  Mr. Adams, played by Mikey Day; the Front Desk Employee, played by Kumail Nanjiani;
  the Government Representative, played by Beck Bennett; and two Room 904 Guests,
  played by Chris Redd and Leslie Jones. Use character names or roles as transcript
  labels, disambiguating the unnamed guests by performer.
processing_instructions: |
  Write exactly two compact synopsis paragraphs. Identify the sketch and all five
  performers with their roles, then explain how the escalating hotel sales pitches
  drive the joke. Give every outline section exactly two concise bullets.
key_terms:
  - Mr. Adams
  - Chatsworth Marriott Experience
  - North Korea
YAML

uv run --locked deep-transcribe \
    --workspace "$DEEP_TRANSCRIBE_E2E_WS" \
    --formatted \
    --metadata "$DEEP_TRANSCRIBE_E2E_WS/fixture/snl-hotel.yml" \
    "$DEEP_TRANSCRIBE_E2E_WS/fixture/snl-hotel.mp3"
```

Inspect the raw transcript before adding exact speaker IDs.
The prose context should be enough for Deep Transcribe to infer the complete five-role
roster and repair boundaries.
Add a `speaker_hints` entry to `snl-hotel.yml` only when one Deepgram ID consistently
belongs to one verified role; for example, use this mapping only if it matches the raw
transcript:

```yaml
speaker_hints:
  "0": Mr. Adams
```

If Deepgram merged distinct voices under one ID, describe the complete speaking roster,
chronology, forms of address, or exact dialogue transitions in `additional_context`
instead of treating that ID as authoritative.
On the normal rerun, verify that Deep Transcribe derives the complete internal roster
and repairs the boundaries.

Use an exact `speaker_roster` only to test the automation override or to correct a
reviewed prose inference:

```yaml
speaker_roster:
  - Mr. Adams
  - Front Desk Employee
  - Government Representative
  - Room 904 Guest (Chris Redd)
  - Room 904 Guest (Leslie Jones)
```

The corrected intermediate transcript must use every roster label, preserve every
timestamped ASR span verbatim, and contain no `UNKNOWN` speaker.
Review short greetings, interjections, and sentence fragments at each speaker boundary.

The annotated HTML must place a two-paragraph synopsis above an always-visible
sans-serif outline. The outline should use the generated section structure and concise
nested bullets rather than reproduce every transcript detail.

Count Deepgram calls, then rerun the annotated pipeline with the corrected metadata.
A speaker-only or descriptive-context correction must not make another Deepgram request:

```shell
DEEPGRAM_COUNT_BEFORE="$(rg -c 'Transcribing via Deepgram' \
    "$DEEP_TRANSCRIBE_E2E_WS/logs/workspace.log")"

uv run --locked deep-transcribe \
    --workspace "$DEEP_TRANSCRIBE_E2E_WS" \
    --annotated \
    --metadata "$DEEP_TRANSCRIBE_E2E_WS/fixture/snl-hotel.yml" \
    "$DEEP_TRANSCRIBE_E2E_WS/fixture/snl-hotel.mp3"

test "$(rg -c 'Transcribing via Deepgram' \
    "$DEEP_TRANSCRIBE_E2E_WS/logs/workspace.log")" = "$DEEPGRAM_COUNT_BEFORE"

test "$(find "$DEEP_TRANSCRIBE_E2E_WS/workspace/resources" \
    -maxdepth 1 -name '*.mp3' | wc -l | tr -d ' ')" = 1
```

This is the normal cache-aware correction path: the metadata change should invalidate
the first affected semantic action and its dependents without forcing unrelated work.
Reserve `--rerun-processing` for a deliberate refresh of every post-transcription stage,
such as a model-profile comparison.

Finally add the real phrase `Stargazer Lounge` to `key_terms` and run `--basic` again.
This accuracy-affecting change must make exactly one new Deepgram request:

```shell
uv run --locked deep-transcribe \
    --workspace "$DEEP_TRANSCRIBE_E2E_WS" \
    --basic \
    --metadata "$DEEP_TRANSCRIBE_E2E_WS/fixture/snl-hotel.yml" \
    "$DEEP_TRANSCRIBE_E2E_WS/fixture/snl-hotel.mp3"

test "$(rg -c 'Transcribing via Deepgram' \
    "$DEEP_TRANSCRIBE_E2E_WS/logs/workspace.log")" = "$((DEEPGRAM_COUNT_BEFORE + 1))"
```

Confirm the raw-file metadata is present in the source sidematter and propagated into
the final transcript frontmatter.
Confirm the correction is reflected in speaker names, description, summary, and headings
without adding unsupported details.

## Local MP4 Frame-Capture Regression

Download the fixture as an MP4 outside a fresh workspace.
Run Deep Transcribe from the repository root, not the fixture directory, so a
basename-only lookup cannot accidentally find the source file in the process working
directory:

```shell
LOCAL_VIDEO_WS="$DEEP_TRANSCRIBE_E2E_WS/local-video"

uv run --locked yt-dlp \
    --format 'bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]' \
    --merge-output-format mp4 \
    --output "$DEEP_TRANSCRIBE_E2E_WS/fixture/snl-hotel.mp4" \
    "$DEEP_TRANSCRIBE_E2E_URL"

test "$PWD" != "$DEEP_TRANSCRIBE_E2E_WS/fixture"

uv run --locked deep-transcribe \
    --workspace "$LOCAL_VIDEO_WS" \
    --annotated \
    --metadata "$DEEP_TRANSCRIBE_E2E_WS/fixture/snl-hotel.yml" \
    "$DEEP_TRANSCRIBE_E2E_WS/fixture/snl-hotel.mp4"

test -z "$(find "$LOCAL_VIDEO_WS/workspace" -type f \
    -name 'snl-hotel.mp4' -print -quit)"
test -n "$(find "$LOCAL_VIDEO_WS/workspace/docs" -type f \
    \( -name '*.jpg' -o -name '*.png' \) -print -quit)"
```

Confirm the source resource is stored as a `file://` reference instead of a full MP4
copy, the run reaches `insert_frame_captures`, and the original remains resolvable for
frame extraction. It must finish without `Original filename not found`,
`Workspace resource not found`, or a full-size source copy in the workspace.
Open the exported HTML and verify the local MP4 frame captures load.

## Careful-Role Model Checks

The annotated pipeline exercises the fast and standard roles.
Check both configured careful models directly so every model in the two profiles is
live-tested:

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
uv run --locked deep-transcribe \
    --models anthropic \
    --workspace "$DEEP_TRANSCRIBE_E2E_WS" \
    --annotated \
    --rerun-processing \
    --language en \
    "$DEEP_TRANSCRIBE_E2E_URL"
```

Confirm the log records `claude-haiku-4-5-20251001` for speaker identification and
formatting and `claude-sonnet-5` for summaries and descriptions.
It must contain no provider authentication, unsupported-model, or malformed-output
error.

## OpenAI Profile

Switch the same workspace to the equivalent OpenAI roles and rerun the annotated path.
The raw transcript cache prevents another paid transcription request while
`--rerun-processing` forces speaker identification, formatting, annotation, and export
to execute again. Reserve `--rerun` for an intentional fresh Deepgram request.

```shell
uv run --locked deep-transcribe \
    --models openai \
    --workspace "$DEEP_TRANSCRIBE_E2E_WS" \
    --annotated \
    --rerun-processing \
    --language en \
    "$DEEP_TRANSCRIBE_E2E_URL"
```

Confirm the log records `gpt-5.6-luna` for speaker identification and formatting and
`gpt-5.6-terra` for summaries and descriptions.
It must contain no provider authentication, unsupported-model, or malformed-output
error.

The optional `--deep` preset also performs paragraph research and may require additional
research-provider credentials.
Run it when that integration is part of the release scope; do not substitute it for the
required annotated run.

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

Have the reviewing model read the reference captions, raw transcription, final Markdown,
and final HTML. Review at least the beginning, middle, and end against the video.
Do not rely only on file sizes or command exit status.

The transcript passes when:

- all statements are present in the right order with no invented content;
- names, job terms, times, and other meaning-bearing words match the audio;
- punctuation and paragraph boundaries are readable;
- Mr. Adams and the Front Desk Employee remain consistently labeled across long turns,
  and the three shorter roles are correctly distinguished;
- no paragraph combines a question and answer from different speakers, except a genuine
  overlap or an isolated brief interjection noted in the report;
- every transcript paragraph has a timestamp near its first spoken word, including the
  first and last paragraphs, and sampled links land within about two seconds;
- speaker identification consistently uses all five expected role labels;
- the annotated output has an accurate description and summary, useful section headings,
  relevant frame captures, and no unsupported claims;
- every exported frame asset is referenced by the HTML, with no rejected
  similarity-filter candidates left in the export directory;
- the HTML renders without raw template syntax, broken links, missing media, clipped
  text, or unreadable styling.

Serve the workspace locally and have the reviewing agent open each provider’s final HTML
export in a browser:

```shell
uv run --locked python -m http.server 8765 \
    --bind 127.0.0.1 \
    --directory "$DEEP_TRANSCRIBE_E2E_WS/workspace"
```

Visually inspect the beginning, middle, and end.
Also inspect the rendered DOM and confirm that every frame image is complete with
nonzero natural dimensions, the page has no horizontal overflow, and no template markers
such as `{{` or `}}` are visible.
Broken or missing frame captures fail the release gate.

Print the final HTML from that browser to PDF with the browser’s headers and footers
disabled and background graphics enabled.
For a reproducible macOS print, use the final absolute HTML path reported by the CLI:

```shell
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --headless=new \
    --disable-background-networking \
    --no-pdf-header-footer \
    --print-to-pdf="$DEEP_TRANSCRIBE_E2E_WS/transcript.pdf" \
    "file:///absolute/path/to/final-transcript.html"
```

Use `google-chrome` or `chromium` as the executable on other platforms.
Inspect the title and outline, a transcript page with frame captures, and the final
page. The outline markers must be aligned, the theme control and table of contents must
be absent, timestamps and the Deep Transcribe footer must remain muted, and no text or
frame may be clipped.

Minor punctuation or filler-word differences may pass when meaning is unchanged.
Any missing phrase, wrong proper noun, mixed-speaker paragraph, shifted timestamp
series, hallucinated summary claim, or repeated processing artifact is a release blocker
until fixed or explicitly accepted by the release owner.

## Timeline and Analytics View

The formatted HTML embeds a transcript index and renders a timeline rail, a speaker
analytics panel, and frame-capture connectors.
Verify in a desktop browser wider than 1450 px unless a step says otherwise.

1. Confirm the page contains one `<script type="application/json"
   id="dt-transcript-index">` element and that its content parses as JSON with
   `version: 1`.
2. Scroll the transcript.
   The rail on the right must keep its reading marker and viewport window in step with
   the text, with no lag or drift, and the speaker band colors must match the colored
   speaker labels in the prose and the Speakers table.
3. Hover the rail at several heights.
   The tooltip must show the timestamp, the speaker name with their color dot, the
   section heading, and opening words from that moment.
4. Click the rail: the page scrolls to that moment.
   Shift-click: the video popover opens at that time.
   With the popover open, the rail must shorten to sit above it.
5. Tab to the rail and press ArrowDown, ArrowUp, Home, and End.
   Each keystroke must move the document one speaker turn or to an end.
6. Hover a frame capture in the gutter: its connector and rail tick must highlight
   together, and hovering the tick must outline the frame.
   Narrow the window below 1450 px: frames must return inline with no connectors, and
   below 1150 px the rail must disappear.
7. Check the Speakers panel: counts and shares must be plausible for the video, every
   speaker must be named in text, and clicking a talk-flow segment must scroll to that
   turn.
8. Toggle light and dark themes: all speaker colors must stay readable in both.
9. Print preview: the printed pages must show no rail, no analytics panel, no
   connectors, and inline frames — identical to the pre-feature layout.
   For the SNL example, compare against
   `docs/examples/snl-hotel-check-in-transcript.pdf` page for page.
10. With reduced motion enabled in the OS, rail clicks must jump without smooth
    scrolling.

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
Timeline and analytics findings:
Material defects or follow-up issues:
Metadata correction and cache findings:
Reviewer verdict:
```

Delete the temporary workspace only after the report is complete:

```shell
rm -rf "$DEEP_TRANSCRIBE_E2E_WS"
```

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
