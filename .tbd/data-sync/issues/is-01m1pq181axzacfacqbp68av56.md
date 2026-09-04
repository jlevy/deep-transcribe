---
type: is
id: is-01m1pq181axzacfacqbp68av56
title: A changed view count re-runs the whole pipeline
kind: bug
status: open
priority: 0
version: 3
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T17:21:32.697Z
updated_at: 2026-09-04T20:32:58.888Z
closed_at: 2026-09-04T18:27:41.939Z
close_reason: "Fixed at the choke point where the source item is built, after the first attempt landed in a branch that never runs for YouTube URLs. Verified: view_count no longer reaches disk, and an unchanged rerun went from a full pipeline to 4 s with zero API calls."
resolution: null
duplicate_of: null
---
Rerunning a source after enough time has passed re-runs the entire pipeline, including
paid speech-to-text, because YouTube's view counter moved.

MEASURED on the same source and workspace:
  a rerun minutes after the first    3 stages ran (concepts, index, minify)
  a rerun about six hours later      every stage ran, including transcription, speaker
                                     correction (33 min), paragraphs (13 min) and
                                     section headings (30 min)

The only meaningful difference in the resource item between those two runs:
    view_count: 1227118  ->  1238631

copy_source_metadata writes the freshly fetched yt-dlp metadata onto the resource item,
view_count is part of item.extra, item.extra is part of item.metadata(), and that is what
every downstream action hashes. So a counter that changes by the minute on a popular
video is inside the cache key of the whole pipeline.

This contradicts what the built-in guide promises — "Updating descriptive context or
speaker metadata preserves speech-to-text", "the normal cache-aware rerun resumes at the
first affected action" — and it defeats the segment-hint loop entirely, since the point
of that loop is that revising a hint costs minutes rather than an hour.

Note view_count is ALREADY deliberately excluded from the prompt context, with a test
asserting it (`assert "view_count" not in context`). So nothing reads it; it only sits in
the identity where it does damage.

FIX: keep volatile counters out of the item metadata that participates in cache identity.
Either drop them when copying source metadata, or hold them somewhere the hash does not
see. Check for siblings before choosing — like_count, comment_count and
channel_follower_count are the same kind of field even if this particular source only
carried view_count.

Worth a test that pins it: copying source metadata twice with a different view_count must
leave item.metadata() unchanged.

## Notes

REOPENED. strip_volatile_source_fields runs on the in-memory item, but prepare_action_input -> fetch_url_item_content has already written the counters to disk via ws.save(overwrite=True). My verification showed view_count: 0 only because I had sed'd the stored resources clean by hand beforehand, which masked exactly the bug. The code comment claiming 'Strip before anything persists the item' is wrong about ordering.
