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

Copy the API key template to a parent directory of the workspace, such as your home
directory:

```shell
cp .env.template ~/.env
```

Set `DEEPGRAM_API_KEY` and one LLM provider key: `ANTHROPIC_API_KEY` for the default
profile or `OPENAI_API_KEY` for the OpenAI profile. See the
[model configuration](../README.md#model-configuration) for current model mappings and
workspace setup commands.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
