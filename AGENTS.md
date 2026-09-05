# Project Instructions for AI Agents

Instructions for AI coding agents working on deep-transcribe.
(This file follows the [AGENTS.md](https://agents.md) convention.
Claude Code reads `CLAUDE.md` instead, which imports this file via its `@AGENTS.md`
line, so edits here reach every agent.)

## Build and Test

This project uses [uv](https://docs.astral.sh/uv/) for Python and dependency management.
The `Makefile` wraps the common commands:

```bash
make install     # uv sync --all-extras --all-groups (install all deps into .venv)
make lint        # auto-format and lint: codespell, ruff check --fix, ruff format, basedpyright
make lint-check  # check-only variant, matching CI (fails instead of fixing)
make test        # pytest plus language-neutral Tryscript CLI goldens
make build       # locked, non-isolated uv build (wheel + sdist)
```

Or call uv directly: `uv run pytest tests/test_foo.py`,
`uv add --exclude-newer "14 days" some-package`, or `uv run python -m deep_transcribe`.

## Conventions

- **Layout**: `src/` layout; code in `src/deep_transcribe/`, tests in `tests/`.

- **Python**: 3.11+ only; use modern typing (full annotations, no `from __future__`).

- **Lint/format**: ruff (line length 100) plus codespell; type checking is
  [basedpyright](https://docs.basedpyright.com/). Settings live in `pyproject.toml`. Run
  `make lint` before committing.

- **Dependencies**: add with `uv add --exclude-newer "14 days"` (runtime) or
  `uv add --dev --exclude-newer "14 days"` (dev).
  Commit `uv.lock`. Don’t use pip, poetry, or requirements.txt.

- **Versioning**: the version comes from git tags via dynamic versioning; never edit a
  version number in `pyproject.toml`. Releases are published to PyPI by tagging `vX.Y.Z`
  (see `docs/publishing.md`).

- This project was built from the
  [simple-modern-uv](https://github.com/jlevy/simple-modern-uv) template; pull future
  template improvements with `copier update`.

See [docs/development.md](docs/development.md) for full developer workflows.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->

<!-- BEGIN TBD INTEGRATION format=f08 surface=agents-md -->
## tbd

This repository uses **tbd** for git-native issue tracking (beads), spec-driven
planning, and on-demand engineering guidelines.
As the agent, you operate tbd on the user’s behalf: translate their requests into tbd
actions rather than telling them to run commands.

- Run `tbd prime` to load current project state and the full tbd workflow.
- Run `tbd skill` for the complete reusable tbd skill instructions.
- Run `tbd shortcut --list` and `tbd guidelines --list` for on-demand resources.
- Track all work as beads: `tbd create`, `tbd ready`, `tbd close`, and `tbd sync`.

<!-- END TBD INTEGRATION -->

<!-- BEGIN DEEP TRANSCRIBE INTEGRATION format=f02 surface=agents-md -->
## Deep Transcribe

Use Deep Transcribe for audio and video transcription and cache-aware refinement.

- In a Deep Transcribe source checkout, run `uv run deep-transcribe --docs`.
- Otherwise, use the installed command only if `deep-transcribe --docs` succeeds.
- If the command is missing or rejects `--docs`, use the exact pinned runner below.
- Use the same verified runner with `--skill` for the complete agent workflow.
- Preserve the same source and workspace when refining a reviewed result.
- Exact pinned runner: `uvx --exclude-newer-package yt-dlp=2026-08-20T00:00:00Z --from "deep-transcribe[youtube]==0.1.14" deep-transcribe`.

<!-- END DEEP TRANSCRIBE INTEGRATION -->
