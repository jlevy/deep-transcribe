# deep-transcribe

Take a video or audio URL (such as YouTube), download and cache it, and perform a "deep
transcription" of it, including full transcription, identifying speakers, adding
sections, timestamps, and annotations, and inserting frame captures.

By default this needs API keys for Deepgram and Anthropic (Claude).

This is built on [kash](https://www.github.com/jlevy/kash) and its
[kash-media](https://www.github.com/jlevy/kash-media) kit of tools for handling videos.

## Usage

See the `env.template` to set up DEEPGRAM_API_KEY and ANTHROPIC_API_KEY.

```
uvx deep_transcribe --help

# Pick a YouTube video, and do a basic or a full transcription:
uvx deep_transcribe full https://www.youtube.com/watch?v=ihaB8AFOhZo
```

## Project Docs

For how to install uv and Python, see [installation.md](installation.md).

For development workflows, see [development.md](development.md).

For instructions on publishing to PyPI, see [publishing.md](publishing.md).

* * *

*This project was built from
[simple-modern-uv](https://github.com/jlevy/simple-modern-uv).*
