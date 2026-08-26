# SPEC-A11-HETEROGENEITY-ATTRIBUTION — Simple metadata diagnosis

Status: research-only revision 1; no selector, confirmation, or promotion authority

## Purpose

This specification binds A11E4, an attribution-only successor authorized after
A11E3. It asks whether the heterogeneous station/member response to the frozen
nearest-candidate forcing adapter is associated with either of two pre-existing
metadata variables: great-circle distance to the selected candidate or whether
the selected candidate and development station share the same registered
climate regime.

A11E4 consumes only closed A11E3 metric evidence and the closed A11E2 selector
receipt. It does not read raw observed series, refit a generator or forcing
model, generate weather, tune a selector, inspect confirmation, or create a
runtime strategy. The frozen attribution regression below is in scope.

## Frozen unit and outcome

The independent analysis unit is the development station. For each of the exact
20 stations, the primary outcome is the fraction of A11E3 members 0–7 for which
nearest-candidate forcing strictly improves both primary metrics relative to
regional-median forcing. The precipitation-only and temperature-only fractions
are descriptive diagnostics. A tie is not an improvement.

Every station must have exactly eight unique members, constant selector
metadata across members, finite metrics, zero invariant failures, and exact
A11E3 strategy identities. The selector receipt must join one-to-one and match
station regime, candidate ID, and distance exactly. Confirmation flags in all
inputs must be false.

## Frozen joint attribution model

The station-level model is

`q = station-regime fixed effects + beta_distance*z_distance + beta_mismatch*mismatch + error`.

Station regimes use UTF-8 order with `arid_boundary` as the reference and five
indicator columns for the remaining registered levels. `z_distance` is the
ascending average rank of exact great-circle distance, centered and scaled by
population standard deviation. `mismatch` is one when station and candidate
regimes differ. The design must have full rank and finite positive residual
variance. Coefficients, two-sided studentized t statistics, full R², and each
predictor's incremental R² are descriptive conditional associations, not
causal effects.

Exact inference permutes the 20 station outcomes within station-regime strata.
The frozen stratum sizes are 2, 4, 4, 2, 4, and 4 in UTF-8 regime order, giving
exactly `2!*4!*4!*2!*4!*4! = 1,327,104` label assignments including identity.
Every assignment refits the same float64 model. The familywise statistic is
`max(abs(t_distance), abs(t_mismatch))`; each predictor's adjusted two-sided
p-value is the fraction of assignments whose max statistic is at least the
observed absolute t for that predictor. The exploratory familywise alpha is
0.05. To include mathematical equality despite batched versus scalar floating-
point evaluation, `>=` comparisons subtract a frozen relative tolerance of
`1e-12 * max(1, observed_threshold)` from each threshold. Runtime verifies that
the identity assignment is actually counted for both predictors.

Observed and stability fits fail closed when residual SSE is at or below the
scale-aware OLS zero tolerance. Permutation assignments use the same tolerance,
but an otherwise valid degenerate assignment follows a frozen conservative
studentization rule: a nonzero selected coefficient maps to signed infinity
(zero maps to zero), so its max statistic counts as extreme against every
finite observed threshold. The number of such assignments is recorded.

A predictor is stable only when its coefficient retains the same strict sign
as the full fit in all eight leave-one-member-out outcome reconstructions and
all twenty leave-one-station-out refits. Leave-one-station-out fits rerank and
rescale distance under the same rule and must remain full rank. A supported
association requires adjusted p <= 0.05 and both sign-stability checks. Nominal
or unstable results remain descriptive.

## Disposition and stop rules

The terminal scientific disposition is exactly one of:

- `SUPPORTED_BOTH_METADATA_ASSOCIATIONS` when both predictors pass;
- `SUPPORTED_DISTANCE_ASSOCIATION` when only distance passes;
- `SUPPORTED_REGIME_MISMATCH_ASSOCIATION` when only mismatch passes; or
- `NO_STABLE_METADATA_ASSOCIATION` when neither passes.

Input, roster, join, finite-value, invariant, runtime, source, replay, or
confirmation-firewall failure fails closed and produces no scientific
disposition. A signal is association, not causal attribution. Correlation
between distance and regime match may make dual signals non-identifying.

A mismatch-only signal may justify proposing one separately authorized,
prospectively fixed same-regime-nearest test. Any distance signal stops for a
material selector/data decision because this evidence cannot choose a distance
cutoff or candidate-pool expansion without tuning. Dual signals do not authorize
combining selector changes. No signal stops simple metadata refinement. No
outcome authorizes confirmation, nomination, promotion, or automatic succession.
