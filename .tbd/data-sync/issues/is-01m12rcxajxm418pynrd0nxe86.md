---
type: is
id: is-01m12rcxajxm418pynrd0nxe86
title: Ship a deno extra so YouTube setup needs no manual JS runtime
kind: feature
status: open
priority: 1
version: 1
labels: []
dependencies: []
parent_id: is-01m0zpq37wdhx51829qx0xmf0t
created_at: 2026-08-27T23:20:34.886Z
updated_at: 2026-08-27T23:20:34.886Z
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
