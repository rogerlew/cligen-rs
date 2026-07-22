# SPEC-A10-EXTERNAL-NORMAL-CONDITIONING

Status: research-only **RATIFIED** (rev 1; A10M5R15 prospective execution
contract; no public runtime identifier)
Authority: [ADR-0006](../decisions/0006-a10-runtime-boundary-expansion.md),
[ADR-0007](../decisions/0007-a10-external-normal-conditioning.md),
[a10-study-plan amendment 2026-07-21](../planning/a10-study-plan.md)

## Surface

Research-only contract for the first externally-normal-conditioned A10
candidate comparison: two matched no-normals/normals pairs evaluated under
the unchanged frozen temporal protocol. The A10M5R15 package ratifies this
revision, its candidate-blind attribution-calibration procedure, resource
bound, and asset-identity preflight before any candidate output.

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
| Adapter pair capacity | E0/E1 use the frozen P2 backbone and the A10M5R14 K2 ceiling of 340,000 total parameters |
| Replacement pair capacity | E2C/E2 replace the P2 backbone; each remains below the architecture-portfolio K2 ceiling of 330,000 total parameters |
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

### E0 — matched E1 control: `centered_location_ou_smooth_climatology-k2`

Exact reconstruction of R14 arm B (bootstrap median regime-ratio upper-90%
2.173, maximum 3.517). No normals input. It is E1's matched attribution
control. R14 arm D remains the stronger prior no-normals incumbent at
2.162/3.517 and stays visible in the report; E0 is not relabeled as that
incumbent.

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

Hypothesis H-E1: measured normals conditioning reduces the bootstrap median
regime-ratio upper-90% relative to E0 by at least the strictly positive,
candidate-blind calibrated attribution margin, with the largest gains in the
annual/monthly location families.

### E2C — matched E2 control: `descriptor_anchored_residual-v1`

E2C is a backbone-free replacement model. A candidate-fit-only deterministic
mapping consumes the five-term day-of-year harmonic basis crossed with
`[1, lat, lon, elev]` and produces all 15 distribution-head baseline
parameters. The R12/R14 medium and slow continuous-time OU factors perturb
only heads 0, 1, 3, and 5. Innovations and decoded offsets are centered over
the exact frozen eight-member evaluation ensemble at every site/day cell.
E2C and E2 share initialization, objective, stochastic fields, dimensions,
training schedule, and non-location baseline surface. E2C is the only valid
no-normals attribution control for E2.

### E2 — `normal_anchored_residual-v1`

E2 is the E2C replacement model with one prospective change: the four
location heads' deterministic mapping additionally receives the 36 measured
monthly normals. It does not contain or initialize from the P2 backbone.

- A frozen mapping, fit only on `candidate_fit` objects, crosses the same
  five-term day-of-year basis with `[1, lat, lon, elev, 36 normals]` for the
  four location heads. The remaining 11 heads use the byte-identical E2C
  descriptor mapping. The mapping is deterministic at generation time and
  hash-pinned after fitting.
- A centered stochastic residual process (medium + slow continuous-time
  OU factors, R12/R14 discretization, no calendar resets) perturbs only
  those baseline location parameters. Centering across the member
  ensemble is structural; the residual cannot relocate the climatology.
- Scale heads, supports, and the wet-amount family
  (`lognormal_wet_v2`) are unchanged. No post-generation repair, no
  realized-month rescaling, no generated-output feedback.

Hypothesis H-E2: measured normals reduce the bootstrap median regime-ratio
upper-90% relative to E2C by at least the same strictly positive,
candidate-blind calibrated attribution margin. The E2/E2C dispersion ratio and
E2/E1 warm-runtime ratio are non-gating diagnostics; they do not claim
preservation of R9's gain or cheaper inference unless measured.

### Exact replacement and fitting contract

The owning package's `artifacts/science-contract.json` is normative for the
replacement pair. E2C uses one bias-free linear `20 -> 15` descriptor baseline
(300 parameters). E2 shares the bias-free `20 -> 11` non-location mapping and
uses a bias-free `200 -> 4` location mapping, for 1,020 baseline parameters.
Both use the byte-inherited R14 continuous OU adapter (1,740 parameters): eight
medium and four slow factors, the R14 time-scale ranges and exact stationary
discretization, no resets, and offsets only on heads 0/1/3/5. Exact totals are
2,040 for E2C and 2,760 for E2.

Both replacement arms use AdamW (`lr=0.001`, weight decay `0.01`), gradient
clip `1.0`, eight differentiable members, six records in each of six batches
per epoch, 24--96 epochs, patience 16, and the same 188-component absolute
scaled objective/checkpoint scalar as R14. Fit validation is gradient-free;
the checkpoint uses the lexicographically first four eligible points per
regime with the inherited `1e-6` earlier-epoch tie rule. Identically seeded
descriptor columns share initialization and E2's normal-only columns begin at
exact zero, so E2C/E2 are output-identical before normals weights update.

### Attribution calibration

Before new candidate output, run the byte-inherited R14 bootstrap operator
twice over the accepted E0 streams with 1,000 replicates and seeds 410542 and
410543. Pair replicate `i` across sequences and compute
`d_i = abs(A_i-B_i)/max(A_i,B_i)`. The shared margin is
`max(1e-6, nearest_rank_q90(d))`, where the zero-based sorted index is 899.
Publish and hash the calibration receipt. For each matched pair, using common
bootstrap seed 410542, compute `g = 1 - treatment_u90/control_u90`; attribution
passes exactly when `g >= margin`. Missing, zero, or non-finite inputs fail.

## Gates and ordering

1. Engineering invariants, provenance, and support gates unchanged from
   the R14 contract; hard failures reject the arm.
2. Temporal eligibility unchanged: bootstrap median regime ratio
   upper-90% ≤ 1.25 and maximum regime ratio ≤ 1.50, both horizons of the
   ratified protocol.
3. Attribution gate: E1 is compared only to E0 and E2 only to E2C with paired
   bootstrap. Before candidate output, the owning package uses candidate-blind
   null/control evidence to freeze one shared strictly positive material-
   improvement margin. Each normals-conditioned arm must clear that margin
   relative to its matched control. Failure is a negative attribution result
   even if other diagnostics move.
4. Runtime classification per ADR-0006 for every arm. The unchanged benchmark
   completes immutable bundle loading, coordinate extraction, normalizer
   application, and station-conditioning construction before the warm timer
   without advancing model or RNG state. E1/E2's per-day normals-conditioned
   mapping evaluation remains inside the warm timer.
5. Confirmation, solar, spatial, and promotion roles remain sealed.

Selection is per treatment, never portfolio-composed. E1 may advance only when
E1 and E0 both pass engineering/runtime, E1 passes both temporal gates, and
E1 clears the E1/E0 attribution margin. E2 uses the identical predicate with
E2C. Passing facts from E1 and E2 cannot be combined into one READY result.

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
