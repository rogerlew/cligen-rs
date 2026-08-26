# SPEC-A12R1-LOCALIZABILITY-AWARE-SELECTION — Feasible Donor Evaluation

Status: research-only revision 1; scaffolded; no runtime authority

## Purpose

A12R1 corrects the prerequisite exposed by A12: a geographically or
climatologically preferred donor can contain monthly occurrence parameters
that the production PRISM localizer cannot transform. It evaluates a single,
explicit feasibility filter before reconsidering policy quality. It does not
silently repair station parameters or reinterpret A12's HOLD.

## Corpus and firewall

Use the same authenticated 240-point A10 `fit_validation` roster, Daymet
calendar/masks, PRISM runtime, `us-2015@2026.07` archive, descriptor families,
build provenance, and confirmation prohibition frozen by SPEC-A12. A new
published source commit, build receipt, execution identifier, and evidence set
are mandatory; A12 artifacts remain immutable.

The immutable predecessor identities are A12 source commit
`d94f6eab53c9103c797b332ae51aea3a87341bcb` and failure-receipt file SHA-256
`ba103ab7d50fbc510910f980181aec9f3a8c188a05cdbee2b7780f7ce567fa7f`.

## Feasibility predicate

For every site and each of its exact nearest ten candidates, run the complete
production six-row localization algebra, F6.2 rendering, f32 reparse, and
encoded constraint validation against that site's PRISM normals. A candidate
is eligible only if every month succeeds. No flooring, imputation, parameter
repair, or fallback outside the nearest ten is allowed in revision 1.

Publish the full 240 × 10 eligibility matrix with source `.par` SHA-256,
failure month/reason where applicable, eligible count, raw-policy selection,
and displacement caused by filtering. If any site has zero eligible candidates,
close on `HOLD-NO-ELIGIBLE-TEN` before quality scoring; pool expansion requires
a separately frozen revision.

## Policies and inference

When every site has at least one eligible donor, compare:

- `closest_localizable_v1`: nearest eligible candidate;
- `cligen_prism_rank_sum_localizable_v1`: the current rank-sum score and tie
  breaks computed over all ten candidates, then the lowest-scoring eligible
  candidate;
- `elevation_prism_reference_localizable_v1`: the A12 elevation/PRISM score
  over all ten candidates, then the lowest-scoring eligible candidate.

The all-ten ranks remain fixed so filtering cannot improve a candidate's score
by renumbering competitors. Use the exact A12 post-localization descriptors,
site pairing, domain-separated 10,000-replicate bootstrap, family safeguard,
and closest-preferred simplicity rule, under a new domain string and seed.
Report feasibility independently from quality; a supported quality policy is
not evidence that a runtime fallback should be automatic.

## Product boundary

The result may recommend a selector candidate for later runtime design. It
does not implement user-defined, closest, fallback, or heuristic CLI modes; it
does not change the current default; and it does not authorize confirmation.

## Provenance and review

Cryptographically bind the exact source commit, locked toolchain build,
executable, registered station archive and extracted tree, PRISM files, all
candidate source `.par` files, calendar objects/shards, preflight, evidence,
decision, and replay. Independent review must reproduce feasibility, selector
choices, metrics, inference, and disposition with no unresolved P0/P1.
