# Feature: Modernize deep-transcribe and Prepare for Release

**Date:** 2026-02-06

**Author:** Claude (with direction from Joshua Levy)

**Status:** Implemented

## Overview

Comprehensive modernization of deep-transcribe: upgrade all dependencies (especially
the kash ecosystem which has had significant new releases), fix code quality issues,
add real tests, and prepare the CLI for a clean new release.

## Goals

- Run `copier update` to pull in latest simple-modern-uv template changes (v0.2.15 →
  v0.2.21, 6 versions behind)
- Upgrade all dependencies to latest stable versions, especially kash-media (0.3.14 →
  0.3.19), kash-shell (0.3.26 → 0.3.37), kash-docs (0.1.14 → 0.1.20), and all other
  outdated packages
- Adapt to any breaking API changes in updated kash dependencies
- Fix known code quality issues (assertions in production code, redundant TYPE_CHECKING
  imports, broad exception handling)
- Add meaningful test coverage (currently only a placeholder test)
- Ensure CLI works end-to-end with updated dependencies
- Update CI/CD configuration (uv version pinning, Python version matrix)
- Clean up and modernize README and docs
- Add Claude Code skill integration (following repren's pattern) so users can invoke
  deep-transcribe naturally from Claude
- Prepare for a new PyPI release

## Non-Goals

- Major new features or new transcription capabilities
- Rewriting the architecture (the current structure is clean and minimal)
- Full 100% test coverage (focus on meaningful tests for core logic)
- Changing the CLI interface or breaking existing user commands

## Background

deep-transcribe is a ~700 LOC Python CLI tool built on the kash ecosystem (kash-shell,
kash-docs, kash-media) for high-quality video/podcast transcription. It uses Deepgram
for transcription and Claude/OpenAI for analysis.

The kash dependencies have been actively developed and have had instability. New stable
versions of kash-shell (0.3.37), kash-docs (0.1.20), and kash-media (0.3.19) are now
available on PyPI. Other dependencies are also behind:

| Package | Current Lock | Latest | Gap |
|---|---|---|---|
| kash-media | 0.3.14 | 0.3.19 | 5 patch versions |
| kash-shell | 0.3.26 | 0.3.37 | 11 patch versions |
| kash-docs | 0.1.14 | 0.1.20 | 6 patch versions |
| flowmark | 0.5.2 | 0.6.2 | 1 minor version |
| prettyfmt | 0.2.1 | 0.4.1 | 2 minor versions |
| rich | 14.0.0 | 14.3.2 | 3 patch versions |
| rich-argparse | 1.7.0 | 1.7.2 | 2 patch versions |
| pytest | 8.3.5 | 9.0.2 | 1 major version |
| ruff | 0.11.9 | 0.15.0 | 4 minor versions |
| basedpyright | 1.29.1 | 1.37.4 | 8 minor versions |

The project is built from the [simple-modern-uv](https://github.com/jlevy/simple-modern-uv)
Copier template, currently at v0.2.15 — 6 versions behind the latest v0.2.21. Running
`copier update` will pull in template improvements to pyproject.toml, CI workflows,
lint config, Makefile, etc.

The codebase also has a few quality issues to address:
- Only a placeholder test exists (`assert True`)
- Production assertions instead of proper validation (`assert result_item.store_path`)
- Redundant TYPE_CHECKING imports in `transcribe_commands.py`
- Overly broad `except Exception` in `get_app_version()`
- Repetitive preset selection logic in `cli_main.py`
- CI pins uv at 0.8.0 which may be outdated

## Design

### Approach

Phased approach: first upgrade and stabilize dependencies, then fix code quality, then
add tests, then prepare for release. Each phase should leave the project in a working
state.

### Key Risk: kash API Changes

The kash ecosystem has had 20+ combined patch releases since the locked versions. The
main risk is that import paths or function signatures may have changed in kash-shell,
kash-docs, or kash-media. After upgrading, we need to:

1. Verify all imports still resolve
2. Check if any kash action signatures changed
3. Check if `kash.config`, `kash.exec`, `kash.mcp`, `kash.model`, `kash.web_gen`, and
   `kash.workspaces` modules are still structured the same way
4. Run linting and type checking to catch issues

### Files to Modify

- `pyproject.toml` — dependency version bumps, possible config updates
- `uv.lock` — regenerated via `uv lock --upgrade`
- `src/deep_transcribe/transcribe_commands.py` — fix TYPE_CHECKING, assertions, adapt
  to any kash API changes
- `src/deep_transcribe/cli_main.py` — fix broad exception, clean up preset logic
- `src/deep_transcribe/transcribe_options.py` — potential minor improvements
- `tests/test_placeholder.py` → `tests/test_transcribe_options.py` + more test files
- `.github/workflows/ci.yml` — update uv version
- `.github/workflows/publish.yml` — update uv version
- `src/deep_transcribe/skills/SKILL.md` — new: Claude Code skill definition
- `src/deep_transcribe/claude_skill.py` — new: skill install/load module
- `README.md` — refresh as needed, add Agent Use section

## Implementation Plan

### Phase 1: Template Update and Dependency Upgrades

- [x] Run `copier update --defaults` to pull in simple-modern-uv template changes
  (v0.2.15 → v0.2.21). Resolve any merge conflicts in pyproject.toml, CI workflows,
  Makefile, etc. Review diff carefully since we have project-specific customizations.
- [x] Bump minimum versions in `pyproject.toml` for all dependencies:
  - `kash-media>=0.3.17` (from >=0.3.14; 0.3.18+ requires Python >=3.13)
  - `flowmark>=0.6.2` (from >=0.5.2)
  - `prettyfmt>=0.4.1` (from >=0.2.1)
  - `rich>=14.0.0` (already fine, minor bumps only)
  - `rich-argparse>=1.7.0` (already fine, minor bumps only)
- [x] Bump dev dependency minimums:
  - `pytest>=8.3.5` (keep compatible with 9.x but don't require it yet)
  - `ruff>=0.15.0` (from >=0.11.9)
  - `basedpyright>=1.37.4` (from >=1.29.1)
- [x] Run `uv lock --upgrade` to regenerate the lock file
- [x] Run `uv sync --all-extras` to install updated deps
- [x] Run linting (`uv run python devtools/lint.py`) and fix any new lint/type errors
  from updated ruff/basedpyright
- [x] Verify all kash imports still work — check for any moved or renamed modules
- [x] Fix any API breakage from kash updates

### Phase 2: Code Quality Fixes

- [x] Remove redundant TYPE_CHECKING block in `transcribe_commands.py` (lines 15-19
  duplicate runtime imports on lines 8-11)
- [x] Replace assertions with proper validation in `format_results()`:
  ```python
  # Instead of: assert result_item.store_path
  # Use: if not result_item.store_path: raise ValueError("...")
  ```
- [x] Narrow exception handling in `get_app_version()` to catch
  `PackageNotFoundError` specifically
- [x] Clean up preset selection logic in `cli_main.py` (simplify the if/elif chain)
- [x] Run full lint + type check to confirm everything passes

### Phase 3: Add Tests

- [x] Replace `test_placeholder.py` with real tests
- [x] Add `tests/test_transcribe_options.py`:
  - Test each preset factory method returns correct flags
  - Test `merge_with()` OR logic
  - Test `from_with_flags()` parsing (valid flags, invalid flags, empty string)
  - Test `get_enabled_options()` returns correct list
- [x] Add `tests/test_cli.py`:
  - Test `build_parser()` produces valid parser
  - Test argument parsing for each preset
  - Test `--with` flag parsing
  - Test that `--mcp`, `--sse`, `--logs` flags work
  - Test URL validation (required unless --mcp)
- [x] Run full test suite and confirm CI-compatible

### Phase 4: Manual E2E Testing and Documentation

- [x] Create a concise `tests/manual-e2e-test.md` documenting how to run deep-transcribe
  end-to-end against a real short (2-3 minute) YouTube video. Include:
  - A specific test video URL (short, public domain or Creative Commons)
  - Commands to run for each preset (`--basic`, `--formatted`, `--annotated`, `--deep`)
  - Expected outputs and what to validate (markdown file, HTML file, frame captures)
  - How to verify the output is clean and complete
- [x] Update `development.md` to be comprehensive for agent-based development:
  - Reference the manual E2E test and when to run it
  - Document the full release process (tag, publish, verify)
  - Document how to run copier update
  - Ensure all workflows are clear enough for an AI agent to follow
- [x] Run the manual E2E test to validate everything works with updated deps

### Phase 5: Claude Code Skill Integration

Modeled after [repren](https://github.com/jlevy/repren)'s skill pattern, make
deep-transcribe installable as a Claude Code skill so users can mention a YouTube
video and ask for a transcription directly from Claude.

- [x] Create `src/deep_transcribe/skills/SKILL.md` with:
  - YAML frontmatter: `name: deep-transcribe`, description, `allowed-tools` (Bash
    for deep-transcribe and uvx invocations, Read, Write)
  - "When to Use" / "Don't Use" sections
  - Quick start examples for each preset (basic, formatted, annotated, deep)
  - Key flags reference table
  - Notes on required API keys (Deepgram, Anthropic)
- [x] Create `src/deep_transcribe/claude_skill.py` with:
  - `get_skill_content()` — reads SKILL.md from package data via `importlib.resources`
  - `install_skill(agent_base=None)` — installs to ~/.claude (global) or project-local
  - Proper error handling for package data access
- [x] Add CLI flags to `cli_main.py`:
  - `--install-skill` — install Claude Code skill (global by default)
  - `--agent-base DIR` — specify agent config directory for skill install
  - `--skill` — print SKILL.md content to stdout
- [x] Add "Agent Use" section to README.md documenting skill installation
- [x] Test skill install flow: `deep-transcribe --install-skill` and verify SKILL.md
  lands in `~/.claude/skills/deep-transcribe/SKILL.md`

### Phase 6: CI/CD and Release Prep

- [x] Update uv version in CI workflows (currently pinned at 0.8.0)
- [x] Verify CI passes on all Python versions (3.11, 3.12, 3.13)
- [x] Review and refresh README if needed
- [x] Confirm `uv build` produces a clean wheel
- [x] Tag and prepare for release

## Testing Strategy

- **Unit tests** (CI): TranscribeOptions logic (presets, merging, flag parsing) — pure
  Python with no external deps
- **CLI tests** (CI): argparse configuration and argument handling — use parser directly,
  no API calls needed
- **Lint/type checks** (CI): ruff + basedpyright as existing CI already runs
- **Manual E2E test** (documented): Run deep-transcribe against a real short YouTube
  video using each preset, validating markdown and HTML output. Requires API keys
  (Deepgram, Anthropic) so not suitable for CI but documented in
  `tests/manual-e2e-test.md` for developers/agents to run before releases.

## Open Questions

- Have any kash import paths changed between kash-shell 0.3.26→0.3.37 or kash-media
  0.3.14→0.3.19? (Will discover during Phase 1)
- Should we require pytest 9.x or stay compatible with 8.x? (Recommend: keep >=8.3.5
  minimum, allow 9.x)
- Are there new kash features we should expose (new transcription actions, new
  formatting options)?
- Should Python 3.14 support be added to the CI matrix?

## References

- [kash-media on PyPI](https://pypi.org/project/kash-media/)
- [kash-shell on PyPI](https://pypi.org/project/kash-shell/)
- [kash-docs on PyPI](https://pypi.org/project/kash-docs/)
- [deep-transcribe on GitHub](https://github.com/jlevy/deep-transcribe)
- [simple-modern-uv template](https://github.com/jlevy/simple-modern-uv)
