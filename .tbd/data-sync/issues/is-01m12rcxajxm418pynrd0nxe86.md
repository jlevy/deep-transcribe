---
type: is
id: is-01m12rcxajxm418pynrd0nxe86
title: Ship a deno extra so YouTube setup needs no manual JS runtime
kind: feature
status: closed
priority: 1
version: 2
labels: []
dependencies: []
parent_id: is-01m0zpq37wdhx51829qx0xmf0t
created_at: 2026-08-27T23:20:34.886Z
updated_at: 2026-08-27T23:44:16.787Z
closed_at: 2026-08-27T23:44:16.786Z
close_reason: "Shipped as the youtube extra: deno>=2.9,<3 in [project.optional-dependencies], locked, and documented as uvx \"deep-transcribe[youtube]\" across README, installation guide, packaged docs, the skill runner, and the AGENTS.md block. Verified: wheel metadata declares Provides-Extra: youtube with Requires-Dist: deno<3,>=2.9; extra == 'youtube', and uv export --extra youtube resolves deno==2.9.5 while the default export resolves none. Kept as an extra rather than a default dependency: no wheels for musl or 32-bit Linux and the sdist is an 8 KB stub, so a hard dependency would break installs there."
resolution: null
duplicate_of: null
---
yt-dlp[default] brings yt-dlp-ejs, the JavaScript solver source, but executing it still needs a JS engine on PATH. The README currently tells the reader to install deno, Node, or bun by hand, which is the only manual step uv cannot cover.

Verified: uv puts the package binary on PATH for the child process.

  uv run --no-project --with deno python -c "import shutil;print(shutil.which('deno'))"
  -> /Users/levy/.cache/uv/archive-v0/rYjKRyLY4q_yQq_h/bin/deno

The deno PyPI package is an official redistribution of the Deno binaries (2.9.6, requires-python >=3.10) with wheels for macOS x86_64/arm64, manylinux aarch64/x86_64, and win_amd64. The arm64 macOS wheel is 38.5 MB.

Proposal: add [project.optional-dependencies] youtube = ["deno>=2.9"] so the documented entry point becomes:

  uvx "deep-transcribe[youtube]" ...

Keep it an extra, not a default: 38 MB is dead weight for local-file transcription. Document 'uvx --with deno deep-transcribe' as the no-packaging-change equivalent.

Open: confirm yt-dlp picks up a PATH deno inside a uvx tool env end to end, and decide whether the skill bundle should default to the extra.
