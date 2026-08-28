---
type: is
id: is-01m133hnx4bgdkyzke16wk6e4n
title: "Upstream: kash web search is a no-op for Anthropic models"
kind: bug
status: closed
priority: 2
version: 2
labels: []
dependencies: []
parent_id: is-01m0zpq37wdhx51829qx0xmf0t
created_at: 2026-08-28T02:35:25.463Z
updated_at: 2026-08-28T04:20:12.793Z
closed_at: 2026-08-28T04:20:12.792Z
close_reason: "Fixed upstream in kash PR #22 and shipped in kash-shell 0.4.10. deep-transcribe's local _web_search_kwargs workaround is deleted; it now calls enable_web_search directly. Verified end to end: 'Enabling Anthropic web search tool', three searches, five-role roster."
resolution: null
duplicate_of: null
---
kash.llm_utils.llm_completion.llm_completion takes enable_web_search, then does two things that together make it inert for Claude models:

1. It gates on litellm.supports_web_search(model=...), which returns False for claude-sonnet-5 and the other Claude names, so the branch never runs. The user gets one warning line, 'Web search requested but not supported by model claude-sonnet-5', and an otherwise normal completion.
2. Even when that gate passes, it sets completion_params['web_search_options'], the OpenAI-shaped parameter. Anthropic does not read it; Anthropic exposes web search as a server-side tool block.

Verified that the capability report is simply wrong: passing tools=[{'type': 'web_search_20250305', 'name': 'web_search'}] through litellm to claude-sonnet-5 performs real searches and returns a sourced answer in about 11 seconds.

deep-transcribe works around this in speaker_correction._web_search_kwargs by routing on provider and passing the Anthropic server tool through kash's existing tools parameter. That workaround should move upstream so other kits get working search, and so the local branch can be deleted.

Suggested fix in kash: drop the supports_web_search gate, or keep it only for providers where the OpenAI-style option is correct, and select the mechanism by provider. Anthropic gets the server tool; OpenAI keeps web_search_options.

Failure mode worth preserving in the fix: today a caller that asks for search silently gets none. Whatever replaces this should fail loudly, or at minimum report which mechanism was used.
