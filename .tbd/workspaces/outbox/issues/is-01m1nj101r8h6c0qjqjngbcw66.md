---
type: is
id: is-01m1nj101r8h6c0qjqjngbcw66
title: Draw concept tracks as clusters, not one bar end to end
kind: task
status: open
priority: 3
version: 2
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T06:34:47.211Z
updated_at: 2026-09-04T08:20:09.546Z
---
A concept's track draws one continuous bar from its first mention to its last. When a
topic genuinely comes up twice, hours apart, that bar claims the whole gap.

MEASURED on Lex #501 after the acknowledgment filter (196226e) removed the false
outliers, four concepts still span more than 15% of the recording, and all four are real:
  0:14:12-3:33:43  AI's superhuman vulnerability-finding   (security at 0:14 and at 3:33)
  1:09:31-3:15:52  Stoicism and Amor Fati
  2:32:10-4:09:15  Glimmers of AGI in agent behavior
  1:50:59-2:41:03  Preference for terminal/TUI harnesses
Each has substantive mentions at both ends. Nothing is wrong with the resolution — the
bar is simply the wrong shape for a topic that recurs.

FIX: draw the track as one segment per cluster of mentions rather than one bar end to
end. Cluster on a gap threshold that scales with the recording (something like the
larger of ten minutes and a small fraction of the duration), so short media clusters
into a single segment and renders exactly as it does today.

The index would carry the clusters alongside the existing span, and `.dt-track-span` in
dt_concepts.js.jinja would render one element per cluster. The span stays for anything
that wants a single extent.

Verify on both examples: the SNL topic tracks must be pixel-identical, and the four
concepts above should each show two segments with a visible gap.

## Notes

OVERTAKEN by chunked extraction. Measured after d73a88d: span median 2.0 min, p90 8.0 min, only 2 of 115 concepts span more than 15% of the recording (was 6 of 24), and just one mention gap exceeds 20 minutes (was 9). A concept now comes from one 30-minute chunk, so its mentions are naturally close together and one bar is an honest shape for almost all of them. Two outliers remain, one at 201 minutes. Not worth the rendering complexity at this rate; revisit only if the count climbs.
