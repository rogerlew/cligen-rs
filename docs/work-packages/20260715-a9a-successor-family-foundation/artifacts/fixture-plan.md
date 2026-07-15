# A9b fixture and recovery plan

Status: freeze-ready A9b implementation contract
Date: 2026-07-15

## Boundary

A9b implements these fixtures before any observed candidate tuning. Fixture
parameters and expected outcomes are synthetic or structural; they are not
estimated from A9 confirmation targets. Passing them proves the harness and
candidate interfaces are executable, not that either candidate is suitable for
observed climate.

Every fixture records schema and source hashes, exact RNG identity, calendar,
row/event counts, expected status, resource ceiling, and canonical metric
bytes. Mutation fixtures fail closed with a typed reason.

## Core fixtures

| ID | Construction | Required result |
|---|---|---|
| FX-001 renewal recovery | Generate 100 synthetic Gregorian years from an alternating wet/dry renewal law with seasonal nongeometric durations, body/tail amounts, adjacent-wet dependence, and event marks. Use four independent fit seeds. | `alternating_renewal_marked_v1` returns `fit_valid`; generating-law duration survival, monthly moments, amount dependence, tail parameters, and descriptor conditionals fall inside the precomputed 95% recovery interval in at least three of four fits. |
| FX-002 latent recovery | Generate 100 years from a three-state hidden semi-Markov law in which every state has strictly interior wet probability and at least one state emits both low and high wet amounts. | `latent_regime_marked_v1` returns `fit_valid`; canonical state ordering is stable and transition/duration/emission targets fall inside recovery intervals in at least three of four fits. |
| FX-003 cross-fit non-isomorphism | Fit both classes to FX-001 and FX-002 and compare likelihood factorization, state paths, and observable objective vectors. | Structural audit confirms no bijective parameter relabeling. Latent occupancy cannot equal observed spell type; renewal has no hidden-state artifact. If either enters the excluded degenerate intersection, return `MODEL-CLASS-EQUIVALENCE`. |
| FX-004 geometric intersection | Generate a geometric two-state wet/dry process with independent exponential amounts, a finite-data intersection both classes can approximate. | Both may match observable metrics; review labels the case finite-data ambiguity, not proof of class identity. Hidden-state and renewal parameter recovery are reported separately. |
| FX-005 zero-scale arid | Include a month with 30 years of zero precipitation and adjacent months with sparse nonzero events. | No standardization/division by zero. Occurrence/zero-month metrics remain available, positive-amount metrics are unavailable, and an unsupported station fit returns `fit_ineligible` without dropping or imputing the month. |
| FX-006 sparse exposure | Supply 24 adjacent-wet pairs and 49 valid events at a station; provide one frozen group below and one above group minima. | Below-group case is `fit_ineligible`; valid group case borrows only registered memory/descriptor parameters and retains station exposure diagnostics. Membership mutation after failure is rejected. |
| FX-007 tail support | Exercise exactly 29 and 30 tail exceedances, boundary shape parameters, and an out-of-support tail proposal. | Twenty-nine makes the tail objective unavailable; 30 activates it; invalid support is `hard_infeasible` before simulation. |
| FX-008 monthly budget | Use analytically tractable independent Bernoulli/gamma marks and dependent two-state marks for 28-, 29-, 30-, and 31-day months. | Reported occurrence, amount, covariance, `E[S]`, and `Var(S)` match analytic values within the frozen quadrature tolerance; a deliberately omitted covariance term fails. |
| FX-009 descriptor collapse | Generate positive-duration events whose input time-to-peak is uniform, then mutate the candidate output to all zeros and separately sever depth/descriptor dependence. | Time-to-peak boundary-mass and joint-dependence objectives fail; no clipping or tie repair occurs. |
| FX-010 event segmentation | Construct five-minute intervals with a 71-interval dry gap, 72-interval gap, missing separation interval, tied peak, cross-midnight event, and cold context. | Exact `a9_uscrn_event_6h_v1` event counts, earliest-tie peak, duration, start-season assignment, and missing-event invalidation match golden JSON. No phase label is created. |
| FX-011 daily context | Send identical precipitation contexts to mock temperature, humidity, radiation, and wind consumers; mutate one context field at a time. | Declared consumers change deterministically, undeclared consumers remain identical, and provenance lists field use. A consumer reading an undeclared field fails interface validation. |
| FX-012 Daymet calendar | Include ordinary/leap-year ordinal records around 28/29 February and 30/31 December. | `daymet_official_365_v1` retains 29 February, omits 31 December in leap years, shifts no value, imputes nothing, and marks affected month/year completeness exactly. |
| FX-013 nonfinite and schema | Mutate every numeric location to NaN, infinity, wrong unit, duplicate key, unknown field/enum, invalid hash, reversed period, or wrong calendar. | Parsing or validation fails before fit, simulation, or metric computation with a stable typed reason. |
| FX-014 RNG domains | Use published Philox key/counter vectors across fit, optimizer, member, simulation, component, date, and variate slots. Add a rejected amount-tail draw. | Golden words reproduce bit-for-bit; domains do not collide; the rejected draw does not shift occurrence, event, another component, or the next date. Faithful state remains unchanged. |
| FX-015 nested horizon | Generate one 100-year stream including leap years and year-crossing spells/events. | The serialized 30-year evaluation rows are the exact prefix of the same 100-year rows; a horizon-dependent plugin is rejected. |
| FX-016 role firewall | Present confirmation path, object hash, logical hash, station-period key, symlink, copied bytes, and renamed object to fit/development/gate commands. | Every route is rejected. Metadata reads append access records but do not change `metadata_only`. Only the confirmation command can atomically consume a complete sealed freeze. |
| FX-017 baseline zero | Supply observed baseline distance zero and positive candidate distance; separately supply a mixed zero-mass distribution. | Absolute-floor and two-part objective rules return finite registered values; no ratio-to-zero, favorable zero, or nonfinite score appears. |
| FX-018 availability | Remove support from one and then two of three synthetic stations in a mandatory stratum. | One unavailable site retains a two-site stratum; two unavailable sites fail mandatory availability. Unavailable is not counted as pass. |
| FX-019 optimizer audit | Terminate normally, crash before checkpoint, crash after checkpoint, exhaust evaluation count, exceed wall time, exceed memory, and resume from a corrupted hash chain. | Complete attempts reproduce; one byte-identical infrastructure retry is allowed; exhaustion is `evaluation_incomplete`; corrupt resume fails; no survivor-only log is possible. |
| FX-020 storage/resource | Force raw streams beyond retention and an artifact beyond 10 MiB. | Only registered replay/failure streams persist, metrics/hashes remain for every attempt, large retained evidence is LFS-covered, and scratch deletion is recorded without deleting evidence identities. |

## Recovery tolerances

A9b must generate tolerances from independent synthetic replications before the
fit code is judged. The tolerance artifact contains at least 200 replications
per recovery fixture, is hash-frozen, and is never recalibrated on observed
data. Scalar parameter coverage must be between 0.90 and 0.99 for nominal 95%
intervals; observable-distribution recovery uses the 95th percentile of
same-law replicate distance. Failure holds A9b rather than relaxing a fixture.

## Mutation coverage

The verifier maps every normative `MUST`/`MUST NOT` in
SPEC-A9-RESEARCH-FOUNDATION to at least one positive or negative fixture.
Schema validation alone is insufficient for cross-file identities,
data-role disjointness, RNG domain separation, monthly-moment reconciliation,
or the one-shot access transition; each receives an executable semantic test.

## A9b exit use

A9b may close `HARNESS-READY-A9C` only when all fixtures pass, both mock class
plugins remain structurally distinct, exact replay/golden vectors are archived,
and no observed target has been accessed. A fixture hold names the first failing
ID and preserves the complete attempt log.
