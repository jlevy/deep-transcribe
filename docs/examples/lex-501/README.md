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
  everything after it. The `replacements` entry here removes the residue:
  `Omachi: Omarchy` cleared all 19 remaining occurrences from the raw transcript body,
  taking Omarchy there from 40 to 59, and editing that list re-runs only the correction
  stage and what follows it.
- `additional_context` and `speaker_roster`: who is speaking and how to label them.
  Changing them re-runs speaker correction and everything after it.
- `processing_instructions`: how the synopsis and outline are written. Changing them
  re-runs only the overview stages.
- `segments.yml`: stretches to mark and keep out of the analysis. Editing an existing
  hint resumes at the outline, about twenty minutes here; the first hints file on a
  source repeats paragraph formatting and section headings once.

Measured cost of the full pipeline with the transcript cached: about 96 minutes.

## Result

Measured on 2026-09-05 with the recipe above, everything cached but the analysis stages
(`--report` output, verified in a browser at 1280×900):

|  | first run of the day, no recipe | with the recipe |
| --- | --- | --- |
| section headings | 206 model headings, one every 1.5 min | 23, the publisher's chapters; 177 model sub-headings under them |
| speaker turns | 1,303 | 753, with 294 one-word acknowledgements folded into the paragraph before them |
| Omarchy misspelled | 102 times, three ways | 0 |
| segments | none | highlight clip and sign-off collapsed and kept out of the analysis; introduction marked |
| synopsis | a topic list | two paragraphs naming both speakers and what each argued, with numbers |
| themes | 13, with one junk theme | 11, none unthemed |
| outline entries | 213 | 164 |
| frames | 173 | 171, none broken |

Cost of getting there: a full run with the transcript cached is 98–104 minutes; an
unchanged rerun is 13 seconds; editing a hint is 20 minutes; a rerun after a stage's
code changed is 19 minutes when that stage's items are set aside first.

What the recipe does not fix, and where it is tracked: a few themes hold one to three
concepts each (dt-6615); a stage whose code changed needs its cached items set aside by
hand until `--rerun-from` exists (dt-8cd9).

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
