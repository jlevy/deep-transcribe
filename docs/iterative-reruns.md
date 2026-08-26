# Iterative Transcription Reruns

A Deep Transcribe workspace is a reusable computation graph.
After the first run, you can inspect the transcript, add context or processing features,
and run the same source again.
Deep Transcribe resumes at the first affected action and reuses compatible media,
speech-to-text, and semantic results.

This workflow is useful when a transcript is broadly correct but needs better speaker
names, more recording context, a different model profile, or another annotation stage.

## Keep the Cache Identity Stable

Reuse both of these values on every iteration:

- the same `--workspace` path
- the same source URL or local media path

Use `--json` so a person or agent can record the workspace, final transcript, and HTML
paths without parsing terminal prose.
Do not delete or replace the workspace between iterations.

For private recordings, keep source-specific metadata beside the media or in another
private directory. Do not copy private paths, participant names, or transcript content
into repository source, tests, documentation, commits, pull requests, or issue records.

## Choose the Smallest Rerun

| Desired change | Command behavior | Speech-to-text behavior |
| --- | --- | --- |
| Change `title`, `description`, `additional_context`, `speaker_hints`, or `speaker_roster` | Run the same command normally; processing resumes at the first affected semantic action | Reuses the cached transcript |
| Add a stage with `--with`, or move from `--basic` to `--formatted`, `--annotated`, or `--deep` | Runs the newly enabled stage and any dependent stages; compatible earlier actions remain cached | Reuses the cached transcript |
| Regenerate all model-derived output or change the saved Anthropic/OpenAI profile | Add `--rerun-processing` | Reuses the cached transcript but forces every later stage |
| Change `key_terms`, language, transcription model, or diarization model | Run normally with the new value | Creates a new transcript cache entry because recognition inputs changed |
| Deliberately repeat every action | Add `--rerun` | Makes a new paid speech-to-text request |

The normal cache-aware rerun is the default.
Do not add `--rerun-processing` or `--rerun` unless the broader refresh is intentional.

## Correct Context and Speakers

Start with the metadata file and command in the
[hotel example](../README.md#end-to-end-example-a-reservation-glitch-and-a-free-jacuzzi).
After reviewing the result, edit the metadata and run the same command again without a
force flag:

```shell
deep-transcribe transcribe \
    --workspace ./output \
    --annotated \
    --metadata ./hotel.yml \
    --json \
    "https://www.youtube.com/watch?v=wyqfYJX23lg"
```

Use the speaker fields according to the evidence:

- Use `speaker_hints` only when a provider speaker ID consistently belongs to one known
  person or role.
- Use a complete `speaker_roster` when the diarizer split one person across IDs or
  merged multiple people under one ID.
- Describe roles, chronology, forms of address, or difficult turn transitions in
  `additional_context`. Do not guess missing names.

Long transcripts are corrected in overlapping windows.
If two windows disagree, Deep Transcribe makes a focused adjudication pass with the
surrounding turns and supplied context.
It still stops rather than guessing if that pass is uncertain.
Add more precise context and rerun from the same workspace in that case.

## Add Processing Features Later

An initial `--basic` transcript can become an annotated or deep transcript without a
second transcription request.
You can also add one stage to the selected preset:

```shell
deep-transcribe transcribe \
    --workspace ./output \
    --annotated \
    --with research_paras \
    --metadata ./hotel.yml \
    --json \
    "https://www.youtube.com/watch?v=wyqfYJX23lg"
```

The new stage runs from the nearest compatible cached result.
Any later stages whose inputs changed are rebuilt.

## Verify Reuse and Output Quality

Inspect the workspace log after each rerun:

```shell
rg -n 'Video transcript already in cache|Transcribing via Deepgram' \
    ./output/logs/workspace.log
```

A semantic-only rerun should log a transcript cache hit, and the number of
`Transcribing via Deepgram` entries should not increase.
Then inspect:

- the final transcript path returned by `--json`
- speaker labels at the beginning, middle, and end
- descriptions, summaries, headings, and any newly requested features
- the rendered HTML, including frame images and timestamp links

Do not treat a zero exit status as a quality review.
Speaker consistency and rendered output still need inspection.

## Ask an Agent to Iterate Safely

Give the agent the source, workspace, requested corrections, and known context.
This prompt template is sufficient:

> Inspect the existing Deep Transcribe result for `SOURCE` in `WORKSPACE`. Update the
> private metadata file with `CORRECTIONS`, then rerun the same preset without
> `--rerun-processing` or `--rerun` so compatible work stays cached.
> Verify that the Deepgram request count did not increase, inspect the corrected
> transcript and rendered HTML at the beginning, middle, and end, and report the final
> artifact paths. Keep all source-specific names, paths, and content out of the
> repository.

If the requested change is a model-profile comparison or a deliberate full semantic
refresh, tell the agent to use `--rerun-processing`. Request `--rerun` only when a new
speech-to-text result is wanted.

## Recover From a Failed Stage

Keep the workspace and rerun the same command after fixing the cause.
Completed upstream actions remain reusable; the failed action has no completed result
and runs again. Check the workspace log before widening the rerun scope.
Deleting the workspace discards this recovery point.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
