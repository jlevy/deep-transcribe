---
title: Deep Transcribe View Design System and Consolidation Refactor
description: The authoritative design rules for the transcript view, and a step-by-step plan to consolidate the organically grown styles into enforced tokens and shared components.
author: Joshua Levy with Claude assistance
---
# Feature: View Design System and Consolidation Refactor

**Date:** 2026-09-03

**Author:** Joshua Levy with Claude assistance

**Status:** Implemented

## Overview

The transcript view’s design settled through rapid owner review: panels, chips,
tooltips, timestamps, and typography each converged on one deliberate treatment.
The rules now live implicitly across `dt_viz.css.jinja` and the dt modules, where they
grew, which makes them easy to drift from.

Per owner direction the design system is self-documenting: the authoritative
reference lives in `dt_tokens.css.jinja` itself, where every token is declared with
its rule beside it and `tests/test_design_tokens.py` enforces the contract.
This spec keeps a summary of the rules and records the consolidation refactor that
moved every literal into tokens and shared helpers.

## Design System Reference

### Typefaces

Serif (PT Serif) is reserved for exactly two things: the literal transcript text and the
page title. Everything else — headings, panels, labels, chips, tooltips, extracted
content such as the summary and glosses — is the sans face (Source Sans 3). Print keeps
the original serif document layout; every screen rule in this system is scoped to
screen.

### Headings

- **H1** heads the page title and every top section (Summary, Timeline, Speakers,
  Outline, Concepts, Claims, Transcript): all-caps, centered, sans, 600 weight, 1rem
  with 0.07em letter spacing.
  The page title alone keeps its serif face and larger size.
- **H2** is used only inside the transcript for section headings: sans, 600 weight,
  1.1rem, text color, upright.
- Panel titles and the outline title render identically to section H1s.

### Text color roles

Exactly three text colors, declared once as tokens; nothing renders text in any other
gray:

| Token | Role |
| --- | --- |
| `--dt-text` | Content: headings, values, glosses, axis numbers |
| `--dt-text-support` | Supporting labels: table headers, research notes |
| `--dt-text-faint` | De-emphasized: bracketed timestamps |

Accent colors come only from the speaker variables (`--dt-c` text-safe, `--dt-cv` vivid
fill) and the concept-kind variable (`--dt-kind-c`).

### Speaker palette

Eight hues, each with a text-safe variant (WCAG AA on both theme backgrounds) and a
vivid fill variant toned to read as the same color.
Fills are used for bands, bars, dots, and markers; text variants for names and labels.
Assignment is by roster order and stable across reruns.

### Concept kinds

A fixed ontology: `topic`, `entity`, `claim` (`decision` folds into claim, `term` into
topic). Kind colors: topic is the site primary, entity the supporting gray, claim the
amber speaker hue. Every concept renders as **the one concept chip**: an outlined box in
the kind color holding the caps kind tag, a dividing bar, and the medium-weight value,
over a very pale kind-tinted background.
One size everywhere — list, Claims, and graph.

### Timestamps

One treatment wherever a time sits inline with other content: light gray
(`--dt-text-faint`), sans, one step smaller, in brackets, clickable with the standard
hover (primary color over hover background).
Clicking a timestamp opens the video at that moment; it never scrolls the page unless no
linkable video exists.
Timeline axis numbers are the exception: bare and full-prominence, because there time is
the content.

### Tooltips

One implementation (`dt_tip`): dark-on-light on the slightly-off page background, a
hairline border, drop shadow, square corners, ~220ms show delay, fade in and out,
viewport-clamped, reduced-motion aware.
Every tooltip target gets the shared hover treatment (brighten and saturate, 120ms);
native title tooltips are never used.
Transcript text inside a tooltip mirrors the prose: colored sans speaker label, serif
words.

### Shape and spacing

Two radii: `--dt-radius` (0.25rem) for controls and `--dt-radius-lg` (0.4rem) for
surfaces. Tooltips are square.
Panels share the outline’s unboxed treatment: 1rem padding, no border.
All time-scaled bars (Timeline overview, per-concept tracks) span the full panel content
width on the same 0-to-duration scale, so bars are comparable across panels.
The transcript prose is inset to the same 1rem text edge.

### Layout

Panel order: Summary, Timeline, Speakers, Outline, Concepts, Claims, Transcript.
Once the views are active, the reading column slides left (center minus 8rem, floored at
2rem or the TOC edge) to reserve the right side for the frame gutter (from 1150px) and
the vertical rail, which stays hidden until the transcript reaches the viewport.
Narrow screens stay centered; print is never affected.

## Consolidation Refactor Plan

No visual changes.
Each step lands separately with the print-parity and test gates green.

- [x] **Step 1 — Token extraction.** Move every token (speaker palette, kind colors,
  text roles, radii, spacing constants) into a dedicated `dt_tokens.css.jinja` with the
  documentation above as comments, imported first by the template.
- [x] **Step 2 — Literal sweep.** Audit `dt_viz.css.jinja` for raw hex values, sizes,
  and one-off grays that bypass tokens; promote or eliminate each.
  The only hex literals allowed live in the tokens file.
- [x] **Step 3 — Shared content builders.** The speaker-head and transcript-excerpt
  tooltip builders exist in three modules (rail, timeline, concepts); extract one helper
  set onto the core model.
- [x] **Step 4 — Hover audit.** Every interactive element either gets a tooltip (which
  applies the standard hover automatically) or explicitly opts into the same hover
  class; remove bespoke hover rules.
- [x] **Step 5 — Enforcement test.** A Python test walks the component sources and fails
  on: hex colors outside the tokens file, `font-family` declarations outside the
  sanctioned rules, radii other than the two tokens, and any `title=` attribute in dt
  module code.
- [x] **Step 6 — Regression pass.** Re-render the SNL test bed in light and dark at 1280
  and 1500 widths, re-run the print comparison against the committed PDF, and spot-check
  the tooltip, selection, and seek contracts in-browser.

## Open Questions

- Should the design reference eventually move into a `docs/design/` page of its own once
  it stabilizes, with this spec keeping only the refactor plan?
- Does upstream kash want any of this (tokens, tooltip, timestamp treatment) once it
  proves out here?

## References

- `docs/project/specs/active/plan-2026-08-31-transcript-timeline-and-concept-map.md` —
  the feature this system grew inside
- `src/deep_transcribe/resources/templates/components/dt_viz.css.jinja` — current
  styles, to be split into tokens plus components
- `src/deep_transcribe/resources/templates/components/dt_tip.js.jinja` — the tooltip
  component

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
