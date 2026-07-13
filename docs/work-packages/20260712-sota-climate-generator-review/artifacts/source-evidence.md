# Source-evidence record

Date: 2026-07-12

This artifact records the reading altitude behind the annotated bibliography.
It separates full-text evidence from claims limited to an official record,
abstract, article HTML, or software release. AB identifiers resolve to
[`sota-climate-generator-annotated-bibliography.md`](../../../lit-reviews/sota-climate-generator-annotated-bibliography.md).

## Full text directly inspected or extracted

- Redistributable corpus: AB-10, AB-13, AB-16–20, AB-24–26, AB-30–32, and
  AB-45–47.
  File identities, versions, licenses, and retrieval URLs are in the
  [`open-access manifest`](../../../../references/open-access/manifest.tsv).
- Local, Git-ignored corpus: AB-02, AB-03, AB-05, AB-06, AB-09,
  AB-12, AB-21–23, and contextual technical note AB-39. File identities are
  committed in
  [`local-reading-copies.tsv`](local-reading-copies.tsv); the PDFs themselves
  are not redistributed.

## Official record, article HTML, abstract, or software release

AB-01, AB-04, AB-07, AB-08, AB-11, AB-14, AB-15, AB-27–29, AB-33–38,
AB-40–44, and AB-48 were evaluated from the DOI-resolved publisher record,
accessible official HTML/full-text surface where available, and official
code/data releases. AB-41's complete USDA-hosted article was inspected;
AB-40 and AB-42–44 remain record/abstract-level evidence.
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
  than being an exhaustive archive of all 48 annotations.

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

## Independent-review additions

Claude's independent review identified missing CLIGEN storm-evaluation and
parameter-coverage literature. AB-40–44 record the primary storm algorithm,
evaluation, fitting, and calibration evidence; AB-45–48 record international,
continental, and near-global parameter products. The archived AB-45–47
versions and licenses are in the open-access manifest. AB-48 remains link-only
because the publisher PDF endpoint rejected automated retrieval; its article
and dataset licenses were verified from official records.

AB-23 remains in the local-reading corpus to identify the exact inspected
copy. Its CC BY-NC-ND 4.0 article license is verified, but the operator chose
not to add another noncommercial/no-derivatives binary to the code repository.
