# SPEC-A10-EXTERNAL-NORMAL-CONDITIONING

Status: research-only **DRAFT** (rev 0; proposed for A10M5R15; not yet
ratified inside an owning package; no public runtime identifier)
Authority: [ADR-0006](../decisions/0006-a10-runtime-boundary-expansion.md),
[ADR-0007](../decisions/0007-a10-external-normal-conditioning.md),
[a10-study-plan amendment 2026-07-21](../planning/a10-study-plan.md)

## Surface

Research-only contract for the first externally-normal-conditioned A10
candidate comparison: one no-normals control and two new candidate
families evaluated under the unchanged frozen temporal protocol. This
draft becomes binding only when the dispatched A10M5R15 package ratifies
it (exact thresholds, resource bound, and asset hashes) before any
candidate output.

## Producers / consumers

Produced by the A10M5R15 trainer/evaluator on Lemhi under
SPEC-LEMHI-AGENT-TOOLKIT admission. Consumed only by the A10 development
record. No production, confirmation, solar, spatial, or promotion
authority.

## Scientific question

Does supplying measured site climate normals — the same information class
the `stochastic_prism_localized_par_v1` reference consumes — close the
site-climatological-location deficit that the R7/R8/R9/R14 record
identifies as the dominant temporal-gate failure mechanism?

## Frozen inputs

| Object | Identity |
|---|---|
| Backbone/capacity | frozen P2 backbone, K2 candidate ceiling (330,000 total parameters), unchanged from A10M5R14 |
| Corpus | accepted A10M1 corpus, 1,200 `candidate_fit` + 240 `fit_validation`, `daymet_official_365_v1` calendar, 16-year windows |
| Normals asset | PRISM Norm91m monthly ppt/Tmax/Tmin bundle, exact SHA-256s inherited from the accepted SPEC-A10-STOCHASTIC-PRISM-COMPARATOR pins, frozen before output |
| Seeds | 147031, 271828, 314159 |
| Temporal protocol | ratified A10M5R4R2 lineage: 6 temporal sites, 8 members × 100 Gregorian years, 1,000 bootstrap replicates, reference = per-regime minimum of faithful and `stochastic_prism_localized_par_v1` |
| Objective | R14 188-component selector-aligned objective, unchanged |
| Runtime rule | ADR-0006 classification (`PASS` < 5.0×, `WARN` 5.0–30.0×, `FAIL` ≥ 30.0×) on the unchanged normative benchmark |

Normals enter the model only after normalization by candidate-fit-only
statistics. The normals values at development/confirmation coordinates
are conditioning covariates under ADR-0007 §3, not target access.

## Arms

### E0 — control: `centered_location_ou_smooth_climatology-k2`

Exact reconstruction of R14 arm B (best accepted result, bootstrap median
regime ratio 2.173, max 3.517). No normals input. Anchors attribution: any
E1/E2 gain is measured against the strongest no-normals candidate, not
against a strawman.

### E1 — `normal_conditioned_smooth_climatology-k2`

Arm B plus normals-augmented climatology. The smooth climatology basis
(outer product of the 5-term day-of-year harmonic vector with site
covariates) extends its covariate list from `[1, lat, lon, elev]` to
include the 36 normalized monthly-normal values (12 months × 3 fields)
read from the frozen bundle at the site coordinate. Heads 0, 1, 3, 5
(occurrence logit, amount log-location, temperature mean, log-DTR
location) as in R14. Everything else — latent OU structure, objective,
seeds, initialization policy — is byte-inherited from arm B. The
parameter delta must stay inside the K2 ceiling and is published in both
adapter-only and total accounting.

Hypothesis H-E1: measured normals conditioning reduces the bootstrap
median regime ratio materially below the E0 control, with the largest
gains in the annual/monthly location families.

### E2 — `normal_anchored_residual-v1`

The R9 design with its diagnosed defect corrected: the deterministic
location baseline is *derived from measured normals*, not learned from 72
regime/month cells.

- A frozen mapping, fit only on `candidate_fit` objects, maps the site's
  36 normal values plus the day-of-year harmonics to the four location
  heads' baseline parameters. The mapping is small, deterministic at
  generation time, and hash-pinned after fitting.
- A centered stochastic residual process (medium + slow continuous-time
  OU factors, R12/R14 discretization, no calendar resets) perturbs only
  those baseline location parameters. Centering across the member
  ensemble is structural; the residual cannot relocate the climatology.
- Scale heads, supports, and the wet-amount family
  (`lognormal_wet_v2`) are unchanged. No post-generation repair, no
  realized-month rescaling, no generated-output feedback.

Hypothesis H-E2: with location owned by measured normals, the residual
mechanism that already demonstrated dispersion gains (A10M5R9, +15.15%)
yields a temporal regime ratio competitive with or below E1 at a fraction
of the backbone's generation cost.

## Gates and ordering

1. Engineering invariants, provenance, and support gates unchanged from
   the R14 contract; hard failures reject the arm.
2. Temporal eligibility unchanged: bootstrap median regime ratio
   upper-90% ≤ 1.25 and maximum regime ratio ≤ 1.50, both horizons of the
   ratified protocol.
3. Attribution gate: E1 and E2 are each compared to E0 with the
   paired-bootstrap machinery; a normals-conditioned arm that does not
   materially improve on E0 (threshold ratified pre-output by the owning
   package) is reported as a negative attribution result even if other
   diagnostics move.
4. Runtime classification per ADR-0006 for every arm; E2's benchmark
   includes the normals-mapping evaluation inside the warm timer.
5. Confirmation, solar, spatial, and promotion roles remain sealed.

If no arm reaches temporal eligibility, the package closes at
`HOLD-A10M5R15-NORMAL-CONDITIONING-NOT-SUFFICIENT` and, per ADR-0007 §
consequences, the record supports adjudicating closure of the neural line
rather than proposing an eighth family.

## Provenance obligations

Every generated stream, checkpoint, and evaluation row records: model
identity, seed, normals bundle identity and SHA-256, normals-window
limitation statement, mapping hash (E2), corpus and calendar identities,
and the ADR-0006 runtime classification. Streams from normal-conditioned
arms are not comparable to descriptor-only lineages without the normals
identity attached.

## Out of scope

Capacity re-entry above K2 (re-admissible under ADR-0006 but deliberately
excluded here so the conditioning variable stays isolated), solar
coupling, N3/elevation expansion, non-CONUS applicability, any Rust
runtime work, and any relabeling of R9/R10 climate-normal families.
