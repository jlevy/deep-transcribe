# Lex Fridman #501 with DHH: a reproducible long-form run

A five-hour interview, used to prove the tool at scale. The two files here are the whole
recipe; the command below reproduces the result, and editing either file is how the
result is improved.

```bash
deep-transcribe --workspace ~/dt/lex-501 --annotated --concepts \
  --metadata docs/examples/lex-501/metadata.yml \
  --segments docs/examples/lex-501/segments.yml \
  "https://www.youtube.com/watch?v=NYFGCESmikA"
```

What each part of the recipe does, and what a change to it costs on this recording:

- `key_terms`: names Deepgram must get right. Without them the transcript spelled
  Omarchy three different ways about eighty times; with the list here, the raw
  transcript has Omarchy 47 times (was 4), Amache 0 (was 14), Hansson 5 (was 1), and
  Omachi 19 (was 25), so a residue remains that only a replacement list would remove.
  Changing them re-runs speech-to-text (about twelve minutes plus the request) and
  everything after it.
- `additional_context` and `speaker_roster`: who is speaking and how to label them.
  Changing them re-runs speaker correction and everything after it.
- `processing_instructions`: how the synopsis and outline are written. Changing them
  re-runs only the overview stages.
- `segments.yml`: stretches to mark and keep out of the analysis. Editing an existing
  hint resumes at the outline, about twenty minutes here; the first hints file on a
  source repeats paragraph formatting and section headings once.

Measured cost of the full pipeline with the transcript cached: about 96 minutes.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
