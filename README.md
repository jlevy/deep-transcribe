# deep-transcribe

High-quality transcription, formatting, and analysis of videos and podcasts.

Deep Transcribe accepts YouTube and other media URLs or local audio and video files.
It uses Deepgram Nova-3 with the current batch diarizer, then can identify speakers,
format paragraphs and timestamps, add sections, write a brief synopsis and structural
outline, research key passages, capture video frames, and export browser-ready HTML.

Speaker attribution drives everything downstream.
Speaker correction, sections, outline, and synopsis all read speaker-labeled text, so
diarization quality sets the ceiling for every later stage.
That is why the backend is Deepgram rather than a transcription-only API such as
OpenAI's `whisper-1`, which returns no speaker labels at all.

LLM processing uses configurable [kash](https://github.com/jlevy/kash) model roles.
New workspaces use the current Anthropic profile by default, and an equivalent OpenAI
profile is included.

## Example: Hotel Check In — SNL

The public example uses the official [Saturday Night Live sketch][example-video]. Its
five speaking roles, short interjections, repeated hotel terminology, running joke, and
scene changes exercise speaker correction, key terms, summaries, outlines, timestamps,
and frame captures in just over four minutes.

| Source Video | Formatted Transcript |
| :---: | :---: |
| [![Mikey Day and Kumail Nanjiani in the SNL Hotel Check In sketch](https://img.youtube.com/vi/kq9Q9-U0vrc/maxresdefault.jpg)][example-video] | [![Formatted Hotel Check In transcript title, synopsis, and outline](docs/examples/snl-hotel-check-in-transcript-preview.png)][example-pdf] |
| [Watch the video][example-video] | [View the PDF][example-pdf] |

[example-video]: https://www.youtube.com/watch?v=kq9Q9-U0vrc
[example-pdf]: docs/examples/snl-hotel-check-in-transcript.pdf

Describe what you know in ordinary prose.
Deep Transcribe gives that context to the speaker-identification and editorial models:

For supported URLs, Deep Transcribe first fetches source metadata through the media
extractor and automatically gives the models a bounded version of the title,
description, canonical URL, and available channel and publication fields.
The context below supplies the complete cast and role relationships that the official
video description does not contain.

```shell
uvx deep-transcribe \
    --workspace ./snl-hotel-output \
    --annotated \
    --title "Hotel Check In — SNL" \
    --context "This is the Saturday Night Live sketch Hotel Check In. The five speaking roles are Mr. Adams (Mikey Day), the Front Desk Employee (Kumail Nanjiani), the Government Representative (Beck Bennett), and two unnamed Room 904 Guests (Chris Redd and Leslie Jones). Label the unnamed roles Room 904 Guest (Chris Redd) and Room 904 Guest (Leslie Jones)." \
    --instructions "Write two short synopsis paragraphs. In the first, identify the SNL sketch and name all five performers with their roles. In the second, explain how the escalating hotel sales pitches drive the joke. Give every outline section exactly two concise bullets." \
    --key-term "Mr. Adams" \
    --key-term "Chatsworth Marriott Experience" \
    --key-term "Stargazer Lounge" \
    --key-term "North Korea" \
    "https://www.youtube.com/watch?v=kq9Q9-U0vrc"
```

The command produces cached media and intermediate results, a processed Markdown
transcript, and browser-ready HTML. Review the result, revise the prose, and run the
same command again to correct context or request a different synopsis or outline.
Use `--context-file notes.txt` when the context is long or will be edited repeatedly.
Deep Transcribe reuses the raw transcript and resumes at the first affected stage.
A cached URL resource created without extractor metadata is enriched on the next run
without repeating speech-to-text.

The static HTML is also the source for the PDF above.
Open it in Chrome or Chromium, choose **Print → Save as PDF**, disable the browser’s own
headers and footers, and keep background graphics enabled.
For an automated, reproducible print on macOS, substitute the absolute HTML path that
Deep Transcribe reports:

```shell
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --headless=new \
    --disable-background-networking \
    --no-pdf-header-footer \
    --print-to-pdf=transcript.pdf \
    "file:///absolute/path/to/transcript.html"
```

Use `google-chrome` or `chromium` as the executable on other platforms.
Deep Transcribe does not require or use a separate PDF renderer.

Run `deep-transcribe --docs` for speaker rosters, cache behavior, custom stages, model
profiles, and deliberate full reruns.

## Getting Started

Deep Transcribe runs through [uv](https://docs.astral.sh/uv/), which fetches Python and
Deep Transcribe itself.
Install uv and [ffmpeg](https://ffmpeg.org/) yourself.
Nothing else needs a manual install.

Speech-to-text always goes through Deepgram, so a
[Deepgram API key](https://console.deepgram.com/signup) is required.
New accounts start with $200 of credit and no credit card.
Add one LLM provider key for the formatting and analysis stages:

- `DEEPGRAM_API_KEY` for speech-to-text and diarization (required)
- `ANTHROPIC_API_KEY` for the default Anthropic profile
- `OPENAI_API_KEY` for the OpenAI profile

Set them in the process environment, a `.env` or `.env.local` file in the current
directory or one of its parents, or `~/.env.local`.
Do not commit API keys.

Then run it without installing anything:

```shell
uvx deep-transcribe --help
```

YouTube sources need a JavaScript runtime, which yt-dlp uses to solve the signature and
`n` challenges YouTube applies to media URLs.
Let uv supply Deno rather than installing a runtime yourself:

```shell
uvx --with deno deep-transcribe URL
```

Deno is the runtime to prefer.
yt-dlp ranks it above Node, QuickJS, and bun, and runs it as the only sandboxed option,
with no network, npm, or local config access.
bun is deprecated upstream.
Deno is also the only one of the four published as an official binary redistribution on
PyPI, which is what lets uv install it alongside Deep Transcribe.
Local audio and video files need no runtime at all.

For repeated use, install it as a persistent tool:

```shell
uv tool install --with deno deep-transcribe
deep-transcribe --help
```

Agents should set up through the skill below, which carries these same steps.

## Cross-Agent Skill

Install the public discovery skill through the cross-agent skills installer:

```shell
npx skills add jlevy/deep-transcribe@deep-transcribe
```

The skill uses the source checkout or installed CLI when available and reads the guide
packaged with that executable.

If the CLI is already available, install its complete skill bundle directly from a
project root:

```shell
deep-transcribe --install-skill
```

This writes the portable `.agents/skills/deep-transcribe/` bundle, the
`.claude/skills/deep-transcribe/` mirror, and a marker-bounded project instruction block
in `AGENTS.md`. The install is idempotent.
Run `deep-transcribe --docs` for surface selection and explicit global-install options.

## Self-Documenting CLI

Start with the single help page:

```shell
deep-transcribe --help
deep-transcribe --docs
deep-transcribe --skill
deep-transcribe --models
```

The help page documents all presets, individual processing stages, Deepgram language and
model selection, natural-language context and exact speaker overrides, caching and rerun
behavior, JSON output, model profiles, and examples.
`--docs` prints the complete guide packaged with the installed release, including the
review-and-rerun workflow and skill installation.
The transcription interface is `deep-transcribe OPTIONS INPUT`.

### Model Provider

Inspect the exact current Anthropic and OpenAI role mappings before selecting one:

```shell
deep-transcribe --models
deep-transcribe --models anthropic
deep-transcribe --models openai
```

The selection is saved in the chosen workspace.
Pass `--workspace` when using a location other than `./transcriptions`. Add an input to
the selection command to save the profile and transcribe in one run:
`deep-transcribe --models openai INPUT`.

## Output

Each run reports:

- the workspace containing cached media and intermediate results
- the transcript source
- browser-ready HTML

Use `--json` when another tool or agent needs stable artifact paths.
You can also open the workspace with `kash` to inspect cached and intermediate items.

## Built-in Guide

Run `deep-transcribe --docs` for the complete operational guide.
It includes environment setup, natural-language context, speaker correction, incremental
reruns, cache verification, model-profile comparisons, output review, privacy,
troubleshooting, and agent-skill installation.
Because the guide ships inside the package, agents can read documentation that matches
the executable they are about to use.

## Project Docs

For environment setup, see [installation.md](docs/installation.md).

For development workflows, see [development.md](docs/development.md).

For the manual, agent-reviewed release test, see
[e2e-test.runbook.md](tests/e2e-test.runbook.md).

For publishing, see [publishing.md](docs/publishing.md).

* * *

*This project was built from
[simple-modern-uv](https://github.com/jlevy/simple-modern-uv).*

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
