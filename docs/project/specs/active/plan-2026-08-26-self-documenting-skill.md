---
title: Self-Documenting, Self-Installing Deep Transcribe Skill
description: Plan for built-in operational docs, cross-agent skill installation, and the hard removal of the MCP server.
author: Joshua Levy with Codex assistance
---
# Feature: Self-Documenting, Self-Installing Deep Transcribe Skill

**Date:** 2026-08-26 (last updated 2026-08-26)

**Author:** Joshua Levy with Codex assistance

**Status:** Complete

## Overview

Make Deep Transcribe explain and install its own agent workflow from the CLI. The
built-in guide will cover the complete transcription lifecycle, especially the important
loop of inspecting a result and rerunning only the model-dependent stages with
additional context or changed features.

This is a hard-cut pre-alpha release.
The MCP server and its compatibility flags will be deleted without aliases, deprecation
warnings, or migration shims.

## Goals

- Add `deep-transcribe --docs` as a complete, packaged operational guide.
- Make iterative reruns a first-class built-in workflow, including context, features,
  stage reuse, output inspection, and cost-saving behavior.
- Add `deep-transcribe --skill` to print a valid, version-pinned `SKILL.md`.
- Add `deep-transcribe --install-skill` for idempotent project-local or explicit global
  installation across portable, Claude, and marker-bounded `AGENTS.md` surfaces.
- Keep one canonical packaged skill source and mechanically generate the public and
  repository-local copies, with drift tests.
- Remove every Deep Transcribe MCP command, flag, implementation path, action export,
  test, and documentation reference.
- Publish and smoke-test a new patch release containing the hard cut.

## Non-Goals

- Preserve any MCP command or flag for backward compatibility.
- Keep a separate long-form iterative-rerun guide that can drift from CLI documentation.
- Install or configure model-provider credentials on the user’s behalf.
- Add a generic plugin, hosted service, or background daemon.
- Redesign transcription, diarization, or model-processing algorithms.

## Background

Deep Transcribe already supports cheap iterative correction: a completed workspace can
reuse cached extraction and Deepgram artifacts while model-dependent stages are rerun
with better speaker context, metadata, prompts, or feature settings.
That workflow is valuable after a human reviews the first output, but today it is split
between the README, a standalone guide, and a manually mirrored skill.

The tbd CLI-backed-skill guidance calls for a local-first, version-pinned, deterministic
skill bundle with explicit install scopes, complete materialization, idempotency,
forward-format protection, actionable failure messages, and drift tests.
Flowmark demonstrates the desired user-facing contract: `--docs`, `--skill`, and
`--install-skill` with portable, Claude, and `AGENTS.md` surfaces.

Deep Transcribe also exposes an MCP server that is no longer part of the desired
product. Because the project is pre-alpha, removal will be direct and complete.

## Design

### Approach

Treat the installed CLI as the source of truth for both humans and agents:

1. Package a concise operational guide with the distribution and print it with `--docs`.
2. Package one authored skill bundle, render its release placeholder deterministically,
   and expose it with `--skill`.
3. Install the same complete rendered bundle with `--install-skill`.
4. Generate checked-in discovery and local-agent mirrors from that canonical source.
5. Delete the MCP surface instead of routing or hiding it.

The skill will stay concise and route detailed operational questions to `--docs` and
command-specific `--help` output.
Its local-first runner will use `deep-transcribe` when available and an exact published
`uvx --from deep-transcribe==X.Y.Z deep-transcribe` fallback otherwise.
The fallback also carries the release’s reviewed per-package yt-dlp cutoff so it remains
resolvable under a user-level uv dependency cool-off.

### Components

- A packaged Markdown guide containing setup, commands, outputs, context, iterative
  reruns, stage reuse, inspection, privacy, and troubleshooting.
- A packaged canonical `SKILL.md` plus `agents/openai.yaml` metadata.
- A Python skill-support module for resource loading, deterministic rendering, release
  pins, complete bundle installation, format markers, and `AGENTS.md` block updates.
- Top-level CLI options:
  - `--docs`
  - `--skill`
  - `--install-skill`
  - `--surfaces=portable,claude,agents-md|all`
  - `--agent-base DIR`
- Generated copies under `skills/deep-transcribe/`, `.agents/skills/deep-transcribe/`,
  and `.claude/skills/deep-transcribe/`.
- Updated README, installation, development, publishing, and design documentation.
- Removal of the `mcp` and `logs` subcommands, MCP compatibility flags, MCP runner, MCP
  action annotations, and their tests.

### API Changes

The following CLI API is added:

```text
deep-transcribe --docs
deep-transcribe --skill
deep-transcribe --install-skill
deep-transcribe --install-skill --surfaces=portable,agents-md
deep-transcribe --install-skill --agent-base ~/.codex
```

Project-local installation defaults to all three surfaces:

- `.agents/skills/deep-transcribe/`
- `.claude/skills/deep-transcribe/`
- A marker-bounded Deep Transcribe block in `AGENTS.md`

`--agent-base` is an explicit single-base installation and is incompatible with
`--surfaces`.

The following CLI API is removed with no compatibility behavior:

```text
deep-transcribe mcp
deep-transcribe logs
deep-transcribe --mcp
deep-transcribe --sse
deep-transcribe --logs
```

The supported direct-source shorthand and `transcribe` subcommand remain transcription
interfaces; they are not compatibility shims for MCP.

## Implementation Plan

### Phase 1: Executable Contract and Tests

- [x] Add failing tests for built-in docs, composed skill output, published-version
  pins, complete installation, target selection, idempotency, forward-format protection,
  `AGENTS.md` preservation, and checked-in bundle drift.
- [x] Add failing CLI tests proving the new options work and the MCP surface is absent.
- [x] Add the packaged guide, canonical skill bundle, and skill-support module.
- [x] Wire the new top-level options into CLI parsing and early-exit dispatch.

### Phase 2: Hard-Cut MCP Removal and Documentation

- [x] Delete MCP and log parsers, compatibility flags, runner code, dispatch paths, and
  MCP action annotations.
- [x] Remove MCP references and consolidate iterative-rerun guidance into `--docs`.
- [x] Update the README and supporting docs to explain self-documentation, skill
  installation, generated-artifact policy, and release maintenance.
- [x] Generate all checked-in skill surfaces from the canonical packaged bundle.
- [x] Validate the skill with the skill-creator validator and format edited Markdown
  with Flowmark.

### Phase 3: Release Validation

- [x] Run focused tests, the full test suite, lint/type checks, and package builds.
- [x] Inspect wheel and source distributions for the complete docs and skill bundle.
- [x] Test the CLI and installer from a built artifact in a clean temporary environment.
- [x] Open and land the pull request after CI passes.
- [x] Tag the next patch release and confirm publication.
- [x] Verify a representative metadata-only transcription rerun reuses the cached raw
  transcript and updates inspected speaker labels.
- [x] Smoke-test the released pinned `uvx` runner for `--docs`, `--skill`, and skill
  installation.

## Implementation Beads

Epic `dt-v7oh` tracks this spec.
Its implementation beads follow the plan’s execution order:

- [x] `dt-dq7h`: Define the built-in documentation and skill contract with tests.
- [x] `dt-gw9f`: Implement packaged documentation and the self-installing skill; blocked
  by `dt-dq7h`.
- [x] `dt-eayp`: Remove the MCP server as a hard cut; blocked by `dt-dq7h`.
- [x] `dt-8mqx`: Consolidate iterative-rerun and skill documentation; blocked by
  `dt-gw9f` and `dt-eayp`.
- [x] `dt-3ka6`: Make the zero-install runner honor the yt-dlp freshness exception;
  blocked by `dt-gw9f`.
- [x] `dt-ulcm`: Validate, land, and release the hard cut; blocked by the original
  implementation, removal, documentation, and packaging beads above.
- [x] `dt-esip`: Make skill runner selection reject stale executables after release;
  blocked by `dt-gw9f`.

## Testing Strategy

Use test-driven development for the public behavior.
Unit tests will cover resource composition, version selection, file generation,
idempotency, conflicting arguments, malformed surface selections, newer-format refusal,
and preservation of host-authored `AGENTS.md` content.

CLI tests will assert that built-in docs contain the iterative-rerun workflow, printed
skill frontmatter is valid, installation reports useful paths and actions, and removed
MCP inputs fail as unknown commands or options.
Drift tests will compare every checked-in bundle with deterministic generated output.

Release validation will build wheel and source distributions, inspect their contents,
install the wheel in an isolated environment, and exercise the self-documenting and
self-installing paths.
A representative cached transcription workspace will verify that the documented rerun
workflow still reuses prior extraction and transcription work.

## Rollout Plan

Merge the hard cut to `main`, tag the next patch version, allow the existing release
workflow to publish it, and verify the published package with an exact version pin.
The discovery skill pin and examples will name that release.
No deprecation period or compatibility layer is required.

## Open Questions

None. The user explicitly approved a hard cut and a new release.

## References

- tbd guideline: `cli-agent-skill-patterns`
- tbd references: `agent-skill-bundle-publication`, `agent-skill-distribution`, and
  `agent-platform-integration`
- Flowmark cross-agent skill plan:
  `/Users/levy/wrk/github/flowmark/docs/project/specs/active/plan-2026-05-27-cross-agent-skill-support.md`
- Flowmark implementation: `/Users/levy/wrk/github/flowmark/src/flowmark/skill.py`
- Agent Skills specification: <https://agentskills.io>

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
