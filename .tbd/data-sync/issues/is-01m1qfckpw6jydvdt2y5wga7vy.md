---
type: is
id: is-01m1qfckpw6jydvdt2y5wga7vy
title: A resumed run names every derived item after the last cached step
kind: task
status: open
priority: 3
version: 1
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-05T00:27:10.939Z
updated_at: 2026-09-05T00:27:10.939Z
---
Observed on dt-final after a --segments edit resumed at the outline: every item the run derived — outline, description, frames, concepts, index, and the export — is named watch_1_step10_insert_section_headings_1_2, _1_4, ... _1_12 and the export is watch_1_step10_insert_section_headings_1_2.html, because kash derives names from the input item and the last cached input was step10. The workspace becomes unreadable (which of six identically-prefixed files is the concept map?) and any tooling that finds items by step name breaks. Either name derived items after the action that produced them, or record the producing action in metadata and surface it. Kash-level behaviour; check whether deep-transcribe's format_results can at least name the export after the final step.
