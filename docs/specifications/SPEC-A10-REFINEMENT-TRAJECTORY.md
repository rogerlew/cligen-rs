# A10 Candidate Refinement and Spatial Promotion Trajectory

Status: research-only

Revision: 1 (ADR-0005, 2026-07-18)

## Surface and authority

This specification defines the prospective A10 successor sequence between
the frozen A10M5 screen and A10M6 development selection. It governs future
family, capacity, realized-dispersion, expanded-corpus, and spatial-
generalization packages. It does not alter A10M3, A10M5, or A10M5R2 evidence,
open a protected data role, select a candidate, or introduce a public
generation profile.

The authorities are ADR-0005, the A10M1 v2 corpus, the A10M3 revision-1 model
and benchmark contracts, A10M5's immutable screen, A10M5R1's clean-process
memory remedy, and the eventual A10M5R2 terminal. A successor machine schema
must be published before its first scored fit.

## Ordered package boundary

The required forward order is:

1. `A10M5R2`: exact corrected-memory replay of the frozen twelve-row screen;
2. `A10M5R3`: candidate-family screen and broad capacity/runtime knee on the
   accepted A10M1 corpus;
3. `A10M5R4`: realized temporal-dispersion adjudication on the accepted corpus;
4. `A10M5R5`: N3/elevation corpus acquisition, leakage audit, role assignment,
   normalization, and immutable transfer freeze;
5. `A10M5R6`: spatially blocked comparison of the two retained capacities; and
6. `A10M6`: final development selection and applicability adjudication.

Passing an earlier package authorizes only its named successor. Confirmation
targets remain unread until the existing A10 sealing procedure authorizes
them.

## Candidate-family screen

The first screen holds pooling and architecture fixed at `N0_complete`, latent
64, width 128, and depth 2 so distribution and station memorization are not
confounded. It uses three prospectively registered fit seeds and these family
classes:

- hurdle Bernoulli plus lognormal positive wet-day amount;
- hurdle Bernoulli plus gamma positive wet-day amount; and
- hurdle Bernoulli plus an explicitly normalized body distribution and GPD
  excess above a frozen threshold.

The prior whole-wet-day GPD is not a legal successor candidate. Every family
must implement and test its own conditional expectation, quantile, sampler,
support, finite-gradient boundary behavior, and empirical sampling
calibration. A splice threshold and its pooling level are derived from
`candidate_fit` only and frozen before `fit_validation` scores are read.

The family screen retains at most two families under a prospectively frozen
proper-score, tail, stability, support, and seed-sensitivity order. A more
flexible family such as generalized gamma, Student-t temperature innovations,
or a positive-amount mixture requires a separate residual diagnosis and new
prospective amendment; it is not an automatic fallback.

## Capacity and runtime knee

The capacity screen uses the winning family and the unchanged A10M1 corpus. It
selects exact legal configurations nearest a prospective geometric ladder of
approximately 35 thousand, 100 thousand, 300 thousand, 1 million, and 3
million parameters. Exact latent, width, depth, parameter counts, seeds, and
job bounds are frozen before allocation. One seed screens the ladder; the two
frontier neighbors receive the additional registered seeds.

For every configuration the evidence records:

- parameter count and portable export bytes;
- GPU fit wall time and peak allocated memory;
- cold-load time;
- clean-process `VmRSS` and `VmHWM` plus external maximum RSS;
- single-core generated days per second at nested 30- and 100-year horizons;
- faithful-relative runtime ratios, dispersion, and absolute safeguards; and
- complete validation, support, stability, and deterministic stream identity.

The capacity decision retains the passing Pareto knee and the immediately
larger passing frontier point. A parameter count alone is not the cost model:
width, recurrence depth, activation/workspace size, and measured CPU work
remain explicit. If no adjacent pair survives, the package holds rather than
manufacturing a spatial pair.

Expanded N3/elevation data are prohibited from this screen. The capacity pair
is provisional until spatial generalization.

## Realized temporal adjudication

Temporal quality is measured from complete generated streams, never from
training-head expectations alone. Calendar-month statistics use actual
Gregorian month partitions. Annual dispersion is the distribution across
generated years and independently seeded members.

The frozen comparison includes observations, faithful CLIGEN, an independently
versioned stochastic generator with PRISM precipitation/Tmax/Tmin monthly
revisions plus `p(W|W)`, `p(W|D)`, and 0.5-hour-intensity adjustments, and each
retained neural capacity. Horizons, members, burns, seeds, station roles,
uncertainty procedure, metrics, and noninferiority/superiority rules are frozen
before output access.

At minimum the adjudication reports:

- monthly precipitation mean, standard deviation, coefficient of variation,
  skew, dry-month frequency, and registered quantiles;
- monthly Tmax/Tmin mean, dispersion, and covariance;
- annual precipitation and temperature mean, dispersion, lag-one dependence,
  and cross-variable covariance;
- `p(W|W)`, `p(W|D)`, wet/dry spell survival, and seasonal dependence; and
- registered annual and 0.5-hour intensity extremes.

"Better dispersion" means smaller error against observations with registered
uncertainty, not simply larger variance. A candidate must satisfy the frozen
noninferiority guards across regimes before aggregate superiority can advance
it.

## N3/elevation corpus and spatial validation

The expanded corpus uses the authoritative North American Level III ecoregion
GIS identity and within-ecoregion elevation strata. Elevation bands are local
quantiles rather than universal meter thresholds. Selection also makes
high-relief valley/midslope/ridge, windward/leeward, rain-shadow, and
coastal/interior contrasts explicit where source coverage permits.

Station roles are assigned by geographic blocks before target values or
derived target statistics are read. Nearby stations cannot cross fit and
evaluation roles through a boundary artifact. Source-network and PRISM-input
overlap are recorded so comparisons are not mislabeled independent.

Continuous candidate descriptors may include latitude, longitude, elevation,
elevation relative to the coarse grid, slope, circular aspect, terrain
position, multiscale relief, coastal distance, and versioned coarse climate
normals. N3 is an acquisition and reporting stratum by default. Making it a
model feature requires an ablation and defined behavior for unseen regions.
Station/tile effects may be retained as training random effects only if unseen-
site inference marginalizes them under a frozen rule.

A10M5R6 trains and evaluates both retained capacities under identical spatial
roles. Random station splits, arbitrary fine-grid output, or in-sample station
embeddings cannot establish better spatial resolution. The required claim is
improvement at geographically held observations over the revised stochastic-
plus-PRISM baseline, including explicit mountain-regime residuals.

## Final architecture and promotion

The final architecture is selected only after temporal and spatial evidence.
The larger retained capacity advances only when its registered spatial or
temporal gain justifies its measured CPU/RSS/export cost. Otherwise the knee
capacity advances. The deterministic rule and all tie breaks are frozen before
A10M5R6 output access.

A10M6 remains unauthorized unless A10M5R2--R6 have honest terminals, at least
one candidate satisfies all hard engineering and climate gates, and the exact
final candidate identity can be reconstructed. Production integration,
confirmation access, and public profile promotion remain later gates.

## Post-A10 boundary

A future cleanroom terrain spatializer is a separate model and interface. Its
intended input is a shared coarse daily stochastic state; its outputs are
terrain-conditioned daily hillslope climates that preserve watershed event
coherence and physical support. Subdaily storm/intensity disaggregation is a
separate downstream layer. Public methods, independently licensed inputs, and
independent tests are authority; an external application's implementation is
not.
