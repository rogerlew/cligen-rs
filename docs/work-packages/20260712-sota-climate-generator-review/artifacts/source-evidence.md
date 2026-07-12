# Source-evidence record

Date: 2026-07-12

This artifact records the reading altitude behind the annotated bibliography.
It separates full-text evidence from claims limited to an official record,
abstract, article HTML, or software release. AB identifiers resolve to
[`sota-climate-generator-annotated-bibliography.md`](../../../lit-reviews/sota-climate-generator-annotated-bibliography.md).

## Full text directly inspected or extracted

- Redistributable corpus: AB-10, AB-13, AB-16–20, AB-24–26, AB-30–32.
  File identities, versions, licenses, and retrieval URLs are in the
  [`open-access manifest`](../../../../references/open-access/manifest.tsv).
- Local, Git-ignored corpus: AB-02, AB-03, AB-05, AB-06, AB-09,
  AB-12, AB-21–23, and contextual technical note AB-39. File identities are
  committed in
  [`local-reading-copies.tsv`](local-reading-copies.tsv); the PDFs themselves
  are not redistributed.

## Official record, article HTML, abstract, or software release

AB-01, AB-04, AB-07, AB-08, AB-11, AB-14, AB-15, AB-27–29, and AB-33–38
were evaluated from the DOI-resolved publisher record, accessible official
HTML/full-text surface where available, and official code/data releases.
Annotations for this group are limited to features, evaluation boundaries,
licenses, and implementation facts stated on those primary surfaces. The
bibliography does not use a secondary source as the sole basis for a ranked
gap.

## Synthesis controls

- Three parallel Codex tasks independently covered the faithful CLIGEN/source
  baseline (`/root/cligen_gap_map`), direct stochastic weather generators
  (`/root/stochastic_wg_survey`), and subdaily/extreme/ML systems
  (`/root/ml_extremes_survey`).
- A separate review disposition records corrections made after those surveys.
- “Published” in the gap analysis identifies external primary-source support;
  it does not imply that every source was locally archived or read from a PDF.
- The open corpus is curated around direct implementation comparators rather
  than being an exhaustive archive of all 39 annotations.

## Local acquisition incorporation

The nine DOI-bearing climate papers in the local reading corpus were
incorporated as full-text evidence on 2026-07-12, and their bibliography access
labels now say so explicitly. Three byte-identical `katz1998*.pdf` files are
alternate copies of AB-02, and `wilks1999.pdf` is an alternate publisher copy
of AB-03; they are not separate evidence items. AB-39 is a distinct USDA
technical note and is recorded as context-only. RNG papers in the same local
directory belong to earlier random-stream research and are outside this
weather-generator review.

The incorporation was independently checked by Codex tasks
`/root/acquired_map` (identity/queue mapping), `/root/fulltext_annotations`
(scientific claims), and `/root/extra_cligen_sources` (duplicates and the USDA
history note).
