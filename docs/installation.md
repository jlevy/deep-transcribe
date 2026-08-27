## Installing uv and Python

This project is set up to use [**uv**](https://docs.astral.sh/uv/), the new package
manager for Python. `uv` replaces traditional use of `pyenv`, `pipx`, `poetry`, `pip`,
etc. This is a quick cheat sheet on that:

On macOS or Linux, if you don’t have `uv` installed, a quick way to install it:

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On macOS, if you prefer [brew](https://brew.sh/), you can install or upgrade uv with:

```shell
brew update
brew install uv
```

See [uv’s docs](https://docs.astral.sh/uv/getting-started/installation/) for more
installation methods and platforms.

Now you can use uv to install a current Python environment:

```shell
uv python install 3.13 # Or pick another version.
```

## Environment Setup

Set `DEEPGRAM_API_KEY` and one LLM provider key in the process environment, a `.env` or
`.env.local` file in the current directory or one of its parents, or `~/.env.local`. Use
`ANTHROPIC_API_KEY` for the default profile or `OPENAI_API_KEY` for the OpenAI profile.
Do not commit the file.

Run `deep-transcribe --models` for the current model mappings and
`deep-transcribe --help` for workspace configuration.

## Install the CLI or Agent Skill

Run Deep Transcribe without a persistent install:

```shell
uvx "deep-transcribe[youtube]" --help
```

The `youtube` extra supplies the Deno runtime yt-dlp needs for YouTube sources.
Plain `uvx deep-transcribe` is enough for local audio and video files.

Users who enforce their own uv supply-chain policy can apply it to this command.

For repeated use, install the CLI and let it materialize its own agent skill from the
project where the skill should be available:

```shell
uv tool install "deep-transcribe[youtube]"
deep-transcribe --install-skill
```

The default skill install targets portable agents, Claude Code, and `AGENTS.md`. Run
`deep-transcribe --docs` for target-selection and explicit global-install examples.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
