---
sandbox: true
env:
  COLUMNS: "80"
path:
  - ../../.venv/bin
patterns:
  VERSION: '\d+\.\d+\.\d+(?:\.dev\d+\+g?[0-9a-f]+)?'
---
# Deep Transcribe CLI Golden Tests

These commands exercise the installed development executable without network or API
calls. The help page is intentionally captured in full so option regrouping, accidental
subcommands, stale examples, and wrapping changes are visible in review.

## Complete Single-Command Help

````console
$ deep-transcribe --help
usage: deep-transcribe [-h] [--version] [--basic] [--formatted] [--annotated]
                       [--deep] [--with STAGES] [--web-search] [--no-minify]
                       [--context TEXT] [--context-file PATH]
                       [--instructions TEXT] [--instructions-file PATH]
                       [--title TEXT] [--description TEXT]
                       [--metadata YAML_OR_JSON] [--key-term TERM]
                       [--speaker ID=NAME] [--speaker-role NAME_OR_ROLE]
                       [--workspace WORKSPACE] [--models [PROFILE]]
                       [--language LANGUAGE]
                       [--transcription-model TRANSCRIPTION_MODEL]
                       [--diarize-model DIARIZE_MODEL] [--rerun]
                       [--rerun-processing] [--json] [--docs | --skill |
                       --install-skill] [--surfaces LIST] [--agent-base DIR]
                       [SOURCE]

High-quality transcription, formatting, and analysis of videos and podcasts

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit

Source:
  SOURCE                YouTube or other media URL, or a local audio or video
                        file

Processing Presets:
  --basic               Transcribe only; no LLM formatting or annotations
                        (basic)
  --formatted           Enable identify_speakers, format (formatted)
  --annotated           Enable identify_speakers, format,
                        insert_section_headings, add_summary_bullets,
                        add_description, insert_frame_captures (annotated)
                        (default)
  --deep                Enable identify_speakers, format,
                        insert_section_headings, research_paras,
                        add_summary_bullets, add_description,
                        insert_frame_captures (deep)

Custom Processing:
  --with STAGES         Comma-separated processing stages to add to the
                        selected preset. Choices: identify_speakers, format,
                        insert_section_headings, research_paras,
                        add_summary_bullets, add_description,
                        insert_frame_captures, web_search
  --web-search, --web_search
                        Let the speaker roster step corroborate facts with web
                        search (off by default; source metadata and your own
                        context are used either way)
  --no-minify, --no_minify
                        Skip HTML, CSS, JavaScript, and Tailwind minification

Natural-Language Guidance:
  --context TEXT        Describe participants, roles, chronology, terminology,
                        and source facts in ordinary prose; repeat to join
                        paragraphs
  --context-file PATH   UTF-8 prose to use as recording context; repeat to
                        join files
  --instructions TEXT   Trusted post-transcription processing instructions;
                        repeat to join paragraphs
  --instructions-file PATH
                        UTF-8 post-transcription processing instructions;
                        repeat to join files

Exact and Structured Overrides:
  --title TEXT          Exact title for the transcript and exported HTML
  --description TEXT    Concise source description to include with the
                        recording context
  --metadata YAML_OR_JSON
                        Optional structured overrides for automation: title,
                        description, additional_context,
                        processing_instructions, key_terms, speaker_hints,
                        speaker_roster, or extra fields
  --key-term TERM       Term or name Deepgram should recognize accurately;
                        repeat as needed
  --speaker ID=NAME     Authoritative speaker label, such as 0='Alice Chen';
                        repeat as needed
  --speaker-role NAME_OR_ROLE
                        Exact speaker name or role for boundary correction;
                        repeat for a complete roster only when prose inference
                        needs an override

Models, Execution, and Output:
  --workspace WORKSPACE
                        Workspace for outputs, metadata, model settings, and
                        caches (default: ./transcriptions)
  --models [PROFILE]    List model profiles with no value, or persist
                        anthropic/openai before an optional transcription
  --language LANGUAGE   Deepgram Nova-3 language code; use 'multi' for
                        multilingual audio
  --transcription-model TRANSCRIPTION_MODEL
                        Deepgram speech-to-text model (default: nova-3)
  --diarize-model DIARIZE_MODEL
                        Deepgram speaker diarization model (default: latest)
  --rerun               Force every stage to rerun, including paid speech-to-
                        text transcription
  --rerun-processing    Force every post-transcription stage to rerun while
                        reusing the raw transcript cache
  --json                Print final workspace and artifact paths as JSON

Built-in Documentation and Agent Skill:
  --docs                Print the complete packaged Deep Transcribe guide
  --skill               Print the version-pinned Deep Transcribe SKILL.md
  --install-skill       Install the skill project-locally to portable, Claude,
                        and AGENTS.md surfaces by default
  --surfaces LIST       With --install-skill: comma-separated portable,
                        claude, agents-md, or all
  --agent-base DIR      With --install-skill: write one explicit
                        DIR/skills/deep-transcribe bundle

**Transcription backend:** Deepgram `nova-3` with `diarize_model=latest`.
Supported language codes:
https://developers.deepgram.com/docs/models-languages-overview#nova-3

Processing stages accepted by `--with`:

- `identify_speakers`: Name speakers using the fast LLM role.
- `format`: Create paragraphs and backfill timestamps.
- `insert_section_headings`: Add topic-based section headings.
- `research_paras`: Add researched paragraph annotations.
- `add_summary_bullets`: Add a concise, section-aligned outline.
- `add_description`: Add a brief two-paragraph synopsis.
- `insert_frame_captures`: Add representative frames for video sources.

**Model provider:** New workspaces use the Anthropic profile. Run
`deep-transcribe --models` to inspect both profiles or
`deep-transcribe --models openai` to persist the OpenAI profile in this
workspace. Add a source to select the profile and transcribe in one invocation.

**Context:** Start with `--context` or `--context-file` in ordinary prose. The
speaker-identification LLM uses those facts to produce its structured mapping.
Supported media URLs also contribute bounded extractor metadata automatically;
use context for relevant facts the source does not publish. When the prose clearly
names the complete set of speaking roles, Deep Transcribe also derives the roster
needed to repair merged diarization boundaries. Exact speaker IDs, repeated
`--speaker-role` values, and YAML/JSON metadata are optional overrides, not the
normal human interface.

**Iterative reruns:** A normal rerun resumes at the first affected stage and
reuses compatible cached work. Updating descriptive context or speaker metadata
preserves speech-to-text. Updating processing instructions resumes at the
overview stages. Changing key terms, the language, or a Deepgram model creates a
new transcription cache entry. `--rerun-processing` forces every post-transcription
stage while preserving the raw transcript. `--rerun` forces every stage,
including speech-to-text.

Examples:

```shell
deep-transcribe --basic ./interview.mp3
deep-transcribe --annotated https://youtu.be/VIDEO_ID
deep-transcribe --deep --language multi URL
deep-transcribe --basic --with format URL
deep-transcribe --context "Alice hosts; Bob presents." URL
deep-transcribe --context-file recording.txt URL
deep-transcribe --speaker 0="Alice Chen" --key-term SignalFlow URL
deep-transcribe --instructions "Keep the outline concise." URL
deep-transcribe --models
deep-transcribe --models openai URL
```

deep-transcribe v0.1.14.dev10+b365c2f
? 0
````

## Model Profile State

```console
$ deep-transcribe --models anthropic --workspace ./output --json && \
> deep-transcribe --models openai --workspace ./output --json && \
> deep-transcribe --models --workspace ./output --json
{"active": "anthropic", "default": "anthropic", "profiles": {"anthropic": {"careful_llm": "claude-fable-5", "fast_llm": "claude-haiku-4-5-20251001", "standard_llm": "claude-sonnet-5", "structured_llm": "claude-sonnet-5"}, "openai": {"careful_llm": "gpt-5.6-sol", "fast_llm": "gpt-5.6-luna", "standard_llm": "gpt-5.6-terra", "structured_llm": "gpt-5.6-terra"}}, "selected": "anthropic", "workspace": "[CWD]/output/workspace"}
{"active": "openai", "default": "anthropic", "profiles": {"anthropic": {"careful_llm": "claude-fable-5", "fast_llm": "claude-haiku-4-5-20251001", "standard_llm": "claude-sonnet-5", "structured_llm": "claude-sonnet-5"}, "openai": {"careful_llm": "gpt-5.6-sol", "fast_llm": "gpt-5.6-luna", "standard_llm": "gpt-5.6-terra", "structured_llm": "gpt-5.6-terra"}}, "selected": "openai", "workspace": "[CWD]/output/workspace"}
{"active": "openai", "default": "anthropic", "profiles": {"anthropic": {"careful_llm": "claude-fable-5", "fast_llm": "claude-haiku-4-5-20251001", "standard_llm": "claude-sonnet-5", "structured_llm": "claude-sonnet-5"}, "openai": {"careful_llm": "gpt-5.6-sol", "fast_llm": "gpt-5.6-luna", "standard_llm": "gpt-5.6-terra", "structured_llm": "gpt-5.6-terra"}}, "workspace": "[CWD]/output/workspace"}
? 0
```

## Invalid Model Profile

```console
$ deep-transcribe --models invalid --workspace ./output 2>&1
usage: deep-transcribe [-h] [--version] [--basic] [--formatted] [--annotated]
                       [--deep] [--with STAGES] [--web-search] [--no-minify]
                       [--context TEXT] [--context-file PATH]
                       [--instructions TEXT] [--instructions-file PATH]
                       [--title TEXT] [--description TEXT]
                       [--metadata YAML_OR_JSON] [--key-term TERM]
                       [--speaker ID=NAME] [--speaker-role NAME_OR_ROLE]
                       [--workspace WORKSPACE] [--models [PROFILE]]
                       [--language LANGUAGE]
                       [--transcription-model TRANSCRIPTION_MODEL]
                       [--diarize-model DIARIZE_MODEL] [--rerun]
                       [--rerun-processing] [--json] [--docs | --skill |
                       --install-skill] [--surfaces LIST] [--agent-base DIR]
                       [SOURCE]
deep-transcribe: error: argument --models: invalid ModelProvider value: 'invalid'
? 2
```

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
