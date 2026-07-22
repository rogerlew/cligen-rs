# ADR-0007: Admit External Measured Climate Normals as Transferable Site Conditioning

Status: Accepted
Date: 2026-07-21
Deciders: Roger Lew (operator)
Evidence:
`docs/work-packages/20260718-a10m5r7r2-authorized-architecture-execution/`,
`docs/work-packages/20260719-a10m5r9-climate-normal-residual-architecture/`,
`docs/work-packages/20260719-a10m5r10-parallel-architecture-portfolio/`,
`docs/work-packages/20260720-a10m5r14r2r2-two-l40-two-wave-portfolio/`, and
`docs/specifications/SPEC-A10-STOCHASTIC-PRISM-COMPARATOR.md`

## Context

Every A10 candidate family to date has been conditioned only on latitude,
longitude, elevation, and frozen regime membership. All of them failed the
frozen temporal selector, and the failures share one diagnosed mechanism:

- A10M5R7R2 attributed the dominant open-loop error to transferable
  seasonal-baseline bias (winter too warm, summer too cold, low
  precipitation quantiles biased) — a site climatological location error,
  not a stochastic-dynamics error.
- A10M5R8R3 showed the objective can buy dispersion only by paying
  location and likelihood inside the current architecture.
- A10M5R9 and A10M5R10 showed a *learned* six-regime × twelve-month
  normal table is too coarse to replace the backbone
  (`HOLD-A10M5R9-RESIDUAL-ARCHITECTURE-NOT-SUPPORTED`; both
  `climate_normal_hierarchical_state_space` capacities failed portfolio
  eligibility) while the residual mechanism itself worked
  (+15.15% dispersion).
- A10M5R14R2R2's only material gain came from the smooth climatology
  basis — a deterministic seasonal basis over just latitude, longitude,
  and elevation — worth a consistent 6–7% median error reduction
  (best candidate 2.162/3.517 against the 1.25/1.50 gates).

Meanwhile the temporal reference the gate divides by is the per-regime
minimum of faithful CLIGEN and `stochastic_prism_localized_par_v1` — and
the latter consumes hash-pinned PRISM Norm91m monthly precipitation, Tmax,
and Tmin normals at the site. The candidates have been asked to beat a
locally calibrated reference while being denied the calibration
information that reference uses. Supplying externally measured normals as
conditioning has been recommended by the R7 disposition but never
executed; the failed R9/R10 families learned normals from 72 fit-corpus
cells, which is a different experiment.

The study plan's architectural envelope (Section 4.2, item 3) already
permits "continuous latitude, longitude, elevation, and climate
descriptors" as conditioning, and its unseen-station rule requires only
that conditioning be transferable and involve "no runtime lookup of a
mutable training database." A frozen, versioned gridded normals product
satisfies both: it is available at any covered site, seen or unseen, and
is immutable once hash-pinned.

## Decision

1. Externally measured monthly climate normals are admissible as
   transferable site conditioning inputs for A10 successor candidates.
   The initial admitted asset is the hash-pinned PRISM Norm91m monthly
   ppt/Tmax/Tmin bundle already versioned under
   SPEC-A10-STOCHASTIC-PRISM-COMPARATOR. Other normals products require a
   new frozen asset identity before use.
2. The normals asset must be frozen, versioned, and hash-pinned before
   any candidate output in the package that consumes it. Runtime
   conditioning is a read of that immutable asset, never a lookup of a
   mutable training database and never derived from generated output.
3. Normals are conditioning covariates, not target values. The
   development/confirmation firewall is unchanged: reading the normals
   surface at a development or confirmation station's coordinates is not
   target access. The overlap between the normals climatology window and
   the evaluation window is recorded as a stated limitation, and every
   package that uses normals conditioning retains a no-normals control
   or ablation so the contribution stays attributable.
4. Candidates conditioned on external normals are new family identities.
   The failed learned-table families (A10M5R9, A10M5R10
   `climate_normal_*`) are not relabeled, rescued, or re-scored.
5. A comparator-anchored residual hybrid is an admissible successor
   family under a new identity: a deterministic normals-derived baseline
   owns climatological location, and a centered neural residual process
   owns dispersion, spells, and dependence. Mean-preservation/centering
   must be structural; post-generation repair, realized-month rescaling,
   and generated-output feedback remain prohibited.
6. This is a deliberate redefinition of the candidate class, accepted
   because the transferable-descriptor-only posture has been exhausted
   across seven families. A10 candidates are no longer claimed to be
   free of site-local climatological inputs; they are claimed to be
   conditionable at any site the frozen normals product covers. The
   applicability envelope inherits the product's coverage boundary
   (CONUS for PRISM Norm91m): stations outside coverage are
   `fit_ineligible` for normal-conditioned candidates and route to the
   declared fallback.

## Consequences

- The pooling-hypothesis vocabulary changes: comparisons between
  normal-conditioned and descriptor-only candidates measure the value of
  measured site climatology, not hierarchical shrinkage. H4-style claims
  must be restated in the owning package before output.
- Reported provenance for any normal-conditioned stream must carry the
  normals product identity and hash alongside the model identity.
- International and out-of-coverage applicability shrinks for this
  candidate class; that boundary is published, not hidden, and faithful
  fallback semantics are unchanged.
- If normal-conditioned candidates still fail the temporal gate, the
  study has isolated the result cleanly: the deficit is not missing site
  calibration, and the defensible record supports closing the neural
  line at its hold rather than proposing further families.
