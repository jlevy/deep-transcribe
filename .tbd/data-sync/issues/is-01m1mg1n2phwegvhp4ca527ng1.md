---
type: is
id: is-01m1mg1n2phwegvhp4ca527ng1
title: Fail fast with setup guidance when API keys are missing
kind: feature
status: closed
priority: 1
version: 3
labels: []
dependencies: []
created_at: 2026-09-03T20:40:57.173Z
updated_at: 2026-09-03T20:44:54.411Z
closed_at: 2026-09-03T20:44:54.410Z
close_reason: Preflight implemented and verified in both directions; .env auto-loading confirmed (repo .env + ~/.env.local both picked up by kash setup); goldens updated
resolution: null
duplicate_of: null
---
Before running the pipeline, check for DEEPGRAM_API_KEY (always) and the LLM key matching the workspace model profile (ANTHROPIC_API_KEY or OPENAI_API_KEY) whenever any LLM stage is enabled. On a miss, exit with a clear message naming the exact variables, where they load from automatically (process env, .env or .env.local in the cwd or parents, ~/.env or ~/.env.local, all loaded by kash at startup), where to create each key, and a pointer to deep-transcribe --docs and docs/installation.md. JSON mode gets a structured error naming the missing variables so an agent can fix it. Custom (non-built-in) model profiles skip the LLM-key check.
