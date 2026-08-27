---
type: is
id: is-01m0zvrk2pytbx4qsk4xfaa4nv
title: Add high-quality browser PDF export
kind: feature
status: in_progress
priority: 1
version: 6
labels: []
dependencies: []
parent_id: is-01m0zpq37wdhx51829qx0xmf0t
child_order_hints:
  - is-01m0zw7p1cq8607eb675yape5m
created_at: 2026-08-26T20:21:40.053Z
updated_at: 2026-08-27T23:50:07.921Z
---
Evaluate existing Kash PDF conversion against standards-based browser print output, define a clean DeepTranscribe export path, preserve print CSS and typography, and verify generated PDFs visually. Keep private acceptance fixtures outside repository records.

## Notes

Acceptance comparison favors printing completed Deep Transcribe HTML with a Chromium-class browser. Browser output preserves title, serif/sans typography, print CSS, project attribution, frame layout, Letter page size, embedded fonts, searchable text, and tagged-PDF structure. Existing Kash create_pdf rewraps the body, scales content, defaults to A4, replaces project attribution, loses the title, emits an untagged PDF, and depends on an unavailable WeasyPrint/native-library stack. The validated acceptance PDF is 84 Letter pages, contains all 120 frames, uses matching 8pt light-gray sans-serif for timestamps and attribution, and has no frame nested inside timestamp brackets or trailing timestamp gap. Remaining work: expose this browser-backed export as a built-in deterministic CLI workflow with browser discovery, stable naming, asset resolution, and clear failure guidance.

Print-CSS findings from regenerating the SNL example PDF (2026-08-27), relevant to the export path:

- Chrome ignores `margin` on `@page` margin boxes entirely. 0.15in and 0.2in render identically. `vertical-align` is the only lever and offers three discrete stops: top, middle (the default look), and bottom, at 0.65in, 0.45in, and 0.24in from the paper edge on Letter. For anything between, put `vertical-align: bottom` on the box and raise `line-height`; the extra leading pushes the baseline up, saturating around 0.31in.
- Margin boxes do not share a baseline unless they share a font size. The footer note was 9pt sans and the page number 12pt serif, which read as misaligned. Equalizing the size fixed it; measured ink-row bottoms then differ by exactly the descender depth.
- Working command, no separate PDF renderer: `Google Chrome --headless=new --disable-background-networking --no-pdf-header-footer --print-to-pdf=out.pdf file:///abs/path.html`. Fonts still load over the network despite --disable-background-networking, and page-relative asset paths resolve, so print in place rather than copying the HTML elsewhere.
- Re-rendering an existing result needs no model calls: load the final doc item from the workspace by store path inside `kash_runtime` and call `format_results`, which re-runs the template and minifier only. Useful shape for the deterministic CLI workflow this bead calls for.
