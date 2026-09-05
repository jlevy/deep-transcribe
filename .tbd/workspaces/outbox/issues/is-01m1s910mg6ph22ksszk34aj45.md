---
type: is
id: is-01m1s910mg6ph22ksszk34aj45
title: Timeline and timestamp clicks must open the player for a public video
kind: bug
status: closed
priority: 1
version: 3
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-05T17:14:28.367Z
updated_at: 2026-09-05T17:47:05.403Z
closed_at: 2026-09-05T17:47:05.403Z
close_reason: --open serves the export from 127.0.0.1 on a free port and opens the browser so the embedded player works; verified over loopback with an asset; LAN refused; six revert probes fail. Verified in the browser on the re-exported page; 1a9f95d.
resolution: null
duplicate_of: null
---
Owner: clicking a timeline block or a timestamp should open the embedded YouTube player; #501 is public. On the export opened via file:// (what 'open' does), enableFileProtocolFallback bypasses the popover because YouTube refuses embeds without a referer (error 153) and makes timestamp LINKS open YouTube in a tab — but timeline block clicks call model.playAt directly and appear to do nothing. Present since PR #18. Fix: (1) under file://, timeline/section/concept clicks must take the same fallback as links (open the video at that time in a tab); (2) verify the embedded popover works over http://; (3) consider a --open flag that serves the export locally and opens it, so the player always works.

## Notes

Verified over http: a timeline block click and a timestamp click both open the yt-popover with the embed at the right start. Under file:// (what 'open' gives), playAt clicks the unit's YouTube link and the fallback opens YouTube in a new tab at the timestamp — YouTube refuses the embed without a referer (error 153). The remaining work is serving the page: an --open/--serve flag so the embedded player always works.
