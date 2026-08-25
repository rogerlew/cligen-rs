# SPEC-A11-EXPLORATORY-STRATEGY-LAB — Versioned exploratory generator strategies

Status: research-only revision 1; no public runtime identifier

## Purpose

This specification defines a flexible A11 development laboratory for trying
multiple non-neural stochastic-generator strategies. It supersedes the failed
one-shot experimental posture of the attempted A11 revision 1 without
rewriting that history. The laboratory produces exploratory diagnostics, not
confirmatory evidence and not a production candidate.

Flexibility is explicit: results from one strategy may motivate another
strategy, different estimators may be compared, and stages may stop early when
they are uninformative. Traceability is equally explicit: a strategy's ID,
algorithm, inputs, evaluator, and source commit are immutable once that
strategy emits observed-data output.

## Strategy lifecycle

Every strategy has one immutable `strategy_id` and passes through:

1. `REGISTERED`: its manifest entry exists in a source commit containing the
   exact implementation and synthetic tests;
2. `PREFLIGHTED`: calendar, role, source, and implementation identities pass;
3. `EXECUTED`: exploratory output is produced from that registered commit;
4. `REVIEWED`: limitations and findings are dispositioned; and
5. `RETAINED` or `RETIRED`: a research-planning label, never a promotion.

Changing a stochastic law, fit estimator, forcing transform, evaluator, or
data role requires a new `strategy_id`. Fixing an operational defect without
changing those surfaces uses a new `attempt_id` under the same strategy. A
manifest revision may add strategies at any time before their output. Previous
exploratory results may be cited as motivation.

## Initial registered strategies

`gaussian_latent_scalar_ar1_v1` pools within-site standardized annual/monthly
anomalies by region, converts them to average-rank Gaussian scores, estimates
one bounded scalar annual persistence coefficient and joint Gaussian
dependence matrix, and samples a stationary vector AR(1) on that latent scale.
This revision deliberately does not invert empirical marginals: exact
population covariance is preferred to an unbounded quadrature approximation.
Location-specific forcing is applied only after sampling latent anomalies.

`circular_fixed_block_bootstrap_v1` resamples complete within-site standardized
annual vectors in fixed-length circular blocks. It preserves empirical within-vector
dependence and short interyear sequences without imposing a Gaussian marginal.
Block length is a manifest field, not an output-selected fallback.

Both strategies use the same deterministic covariance reconciliation and
conditional daily core. They may be evaluated independently; neither is a
fallback for the other.

The `annual_monthly_targets` capability in revision 1 means continuous states
on a registered modeling scale. It is deliberately field-agnostic and does not
claim a physical precipitation/range/count adapter. Physical precipitation
totals and integer wet counts enter only through the support-valid daily-core
interface. A later strategy or adapter must declare any log, bounded, integer,
or other physical-scale transform before making integrated forcing claims.

Revision 1 binds both strategies to evaluator `a11e_core_diagnostics_v1`,
metric set `a11e_core_metrics_v1`, and uncertainty method
`a11e_descriptive_bootstrap_v1`. These identifiers describe research
interfaces in this package; their observed-data implementations must be
present in the source commit used for execution.

## Shared numerical surfaces

### Within-site variation fitting

For each field and fit site, subtract that site's 30-year mean and divide by
its sample standard deviation. Constant fields fail closed. Pool only these
standardized anomalies by registered region. This prevents between-site
climatology from masquerading as interannual variation.

### Covariance reconciliation

Given fixed monthly variances, a requested covariance shape, annual weights,
and requested annual variance, move along the affine line from the diagonal
matrix to the requested covariance. The effective scalar is the value nearest
the requested annual target inside the positive-semidefinite interval. The
receipt records the requested/effective scalar, annual variance, minimum
eigenvalue, tolerance, and whether boundary projection occurred. Monthly
variances remain exact.

Requested covariance must already be finite, symmetric, and have the declared
monthly variances on its diagonal; discrepancies fail closed. If the annual
functional is insensitive to the requested off-diagonal structure and the
annual target already equals the diagonal contribution, the tie rule preserves
that requested structure (`alpha = 1`).

Reconciliation is a stationary population-law claim, not a forced finite-run
sample moment. Each strategy deterministically records the mean and covariance
of its generated anomaly law: the fitted Gaussian correlation for the latent
strategy and the uniform-row population moments for the circular block
strategy. Sampling is centered and whitened against those fixed moments before
the effective covariance and location are applied. The
transform is prefix-consistent and works when fields outnumber years. Receipts
separately report realized finite-sample covariance and discrepancy as sampling
diagnostics; they never relabel those realized moments as exact targets.

### Joint precipitation/wet-count support

Wet count is sampled from a registered empirical integer distribution already
conditioned on the sampled precipitation total's feasible set. Zero total maps
only to zero wet days. A positive total requires a count between one and both
the month length and `floor(total / wet_threshold)`. Absence of a feasible
fitted count fails closed; a sampled target is never repaired afterward.

### Conditional daily core

The shared core provides an exact-count first-order Markov bridge, positive
wet-day amounts with one exact-total allocation, a centered/scaled AR(1)
temperature residual, and a positive monthly-mean-preserving range process.
Storm descriptors and secondary variables are separate strategy capabilities.
A strategy that lacks them may run core-climate diagnostics but is ineligible
for WEPP or integrated claims. Capability absence is explicit in the manifest.

## Exploratory evaluation

Stages are diagnostic rather than pass/fail confirmation gates:

- synthetic invariants and moment recovery;
- candidate-fit cross-validation;
- role-correct held-out development diagnostics;
- optional storm/context and WEPP diagnostics only for strategies declaring
  those capabilities.

Metrics and uncertainty methods are versioned in each strategy entry. Results
may inform later strategy design. No threshold in this laboratory authorizes
confirmation access, production profile registration, default changes, or a
promotion claim.

## Data and provenance

Observed-data execution requires the canonical Daymet calendar preflight from
`SPEC-A10-CORPUS`: exact ordered Gregorian axis, 10,958 axis rows, 10,950
observed rows, eight masked leap-year December 31 rows, explicit boundaries,
per-object required-field masks, and month/year eligibility.

Every execution binds the full source commit that already contains the
manifest, implementation, tests, evaluator, and schema; their individual
SHA-256 identities; input manifests and roles; strategy and attempt IDs; RNG
algorithm/domains; resource use; and artifact hashes. Working-tree or
untracked-source scientific execution is invalid.

## Confirmation and production boundary

This laboratory has no confirmation consumer and no promotion authority. A
later confirmatory package must select and freeze one retained strategy before
accessing a separately authenticated confirmation corpus. Faithful CLIGEN and
all public profiles remain unchanged.

## Failure behavior

Malformed shapes, non-finite values, constant fit fields, duplicate or unknown
IDs, source/hash drift, role/calendar drift, infeasible wet-count support,
non-PSD unreconciled covariance, random-domain collisions, missing declared
capabilities, and incomplete provenance fail closed. Exploratory retirement is
not a scientific rejection of the entire strategy family.
