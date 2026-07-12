# State-of-the-Art Climate Generator Review

Status: `EXECUTED-COMPLETE`
Date: 2026-07-12
Evidence mode: Mixed

## Objective

Establish a primary-source, implementation-oriented comparison of modern
weather and climate generators; rank the resulting capability gaps relative
to faithful CLIGEN; translate the ranking into feasible `cligen-rs` work; and
publish a DOI-first annotated bibliography and legally redistributable source
corpus suitable for the public repository.

## Scope

Included:

- point, multisite, gridded, subdaily, extreme-event, nonstationary, and
  multivariate stochastic weather generators;
- representative generative-ML forecast, climate-emulator, and downscaling
  systems needed to define the comparison boundary;
- the faithful CLIGEN capability baseline and repository-measured gaps;
- ranked scientific gaps, implementation seams, data needs, risks, validation
  requirements, and package ordering;
- DOI-first annotations, an operator-acquisition queue, and open-access source
  provenance.

Excluded:

- selection or implementation of a new generation profile;
- silent changes to faithful behavior or the legacy `.par` contract;
- redistribution of papers without verified reusable terms;
- treating single/design-storm mode as a constraint on the first extension.

## Authority

- Faithful CLIGEN claims: `reference/cligen532/cligen.f`,
  `docs/specifications/SPEC-FAITHFUL-GENERATION.md`, and its traceability
  package.
- Measured quality claims: the Q3/Q4 package artifacts and active quality
  specification.
- Comparative claims: the primary papers and official software records cited
  in the annotated bibliography. Preprints are labeled as such.
- This review is informational. It is not a generation-profile decision or an
  interface specification.

## Plan

1. Establish the faithful CLIGEN capability and evidence baseline.
2. Survey directly comparable daily stochastic generators.
3. Survey subdaily/extreme/spatial systems and representative generative-ML
   systems.
4. Rank gaps by WEPP relevance, evidence, feasibility, and prerequisite risk.
5. Map the ranking to `cligen-rs` seams, packages, data, and validation gates.
6. Publish the review, annotations, and licensed source corpus.

## Execution & dispatch

Executed on `main`; started from current `origin/main`; push target is `main`.
Codex synthesized the review. Parallel read-only tasks covered the local
CLIGEN gap map (`/root/cligen_gap_map`), directly comparable stochastic
generators (`/root/stochastic_wg_survey`), and ML/extreme systems
(`/root/ml_extremes_survey`).

## Gates

- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`
- Every ranked gap is marked measured, source-proven structural, or proposed.
- Every annotated paper has a DOI or an explicit no-DOI note.
- Every redistributed PDF has a verified reusable license and SHA-256 entry.
- License-unclear/paywalled sources are DOI/link-only.
- ML forecast/emulator systems are not represented as direct CLIGEN peers.

## Exit criteria

Achieved 2026-07-12: the gap analysis and annotated bibliography are present;
the source manifest identifies all archived articles and licenses; the first
implementation sequence is concrete; and repository gates passed as recorded
in `artifacts/gate-results.md`.

## Artifacts

- `../../lit-reviews/sota-climate-generator-gap-analysis.md`
- `../../lit-reviews/sota-climate-generator-annotated-bibliography.md`
- `../../../references/open-access/manifest.tsv`
- `artifacts/gate-results.md`
- `artifacts/local-reading-copies.tsv`
- `artifacts/source-evidence.md`
- `artifacts/review.md`
