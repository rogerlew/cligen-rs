# A5d0 Feasibility Analysis

Status: `EXECUTED-HOLD-CONTRACT-INCOMPLETE`
Evidence mode: Derived and static
Evidence boundary: deterministic synthetic fixtures and exposed A5a/A5b
development evidence only; no A5d confirmation candidate output

## Finding

A whole-year/block selector can reallocate variance in principle, but the
candidate class is not yet freeze-ready. The constructive fixture preserves
the daily mean and second moment while increasing between-year variance by
40% and decreasing within-year variance by the same absolute amount. A
persistent transition kernel can then add lag covariance without changing its
stationary block weights. Those results establish mathematical capability,
not feasibility for an arbitrary faithful CLIGEN library.

Two fixture results show why the existence proof is insufficient:

1. if selectable years have constant within-year variance, preserving the
   daily mean and second moment also fixes between-year variance; and
2. the simple persistent kernel used to prove stationarity repeats the exact
   same block with probability 0.6778, while no reuse ceiling has yet been
   prospectively adjudicated.

Neither fixture disproves feasibility for the actual faithful libraries. `GO`
is blocked because no actual-library constrained solution, bounded repeat-safe
path algorithm, or prospectively fixed reuse ceiling exists. The missing
algorithm must also satisfy exact seed semantics, calendar classes, and the
common 30-/100-year prefix. A5d therefore cannot freeze a candidate version
from this package.

## Authority and inputs

- ADR-0004 requires analytic feasibility before another campaign.
- A5b's accepted results are exposed development evidence. They show universal
  failures in monthly preservation, daily precipitation structure, and storm
  descriptors, but they are not reused to rank a successor.
- The deterministic results are in
  [`feasibility-fixtures-v1.json`](feasibility-fixtures-v1.json), reproduced by
  [`run-feasibility-fixtures.py`](run-feasibility-fixtures.py).
- All accepted inputs are fixed by
  [`evidence-lock-inputs-v1.json`](evidence-lock-inputs-v1.json).

## Variance budget

Let `X` be a daily value from a selected year/block and `S` its selected annual
state. Then

```text
Var(X) = E[Var(X | S)] + Var(E[X | S]).
```

The first term is within-state or within-year variability; the second is
between-state variability. A candidate cannot increase the second term while
holding total variance fixed unless it decreases the first term. That is the
precise distinction between variance reallocation and the A5b multiplicative
overlay, which added between-year variation without compensating the existing
within-year term.

For the equal-length fixture, let `w_i` be stationary year-selection weights,
`mu_i` a block mean, and `q_i` the pooled daily second moment. It preserves

```text
sum_i w_i       = 1
sum_i w_i mu_i  = target mean
sum_i w_i q_i   = target second moment,
```

then maximizing `sum_i w_i mu_i^2` reallocates variance toward the annual
component. With fixed target means, the mean, raw-second-moment, wet-frequency,
transition, and analogous cross-variable conditions can be written as linear
constraints on `w`. Feasibility is nevertheless library-specific: the annual
second-moment vector can lie in the span of the preservation constraints, in
which case its value cannot move.

Production constraints must weight physical daily observations, not years.
For block length `n_i`, daily mean and second-moment preservation take forms

```text
sum_i w_i n_i (mu_i - mu_target) = 0
sum_i w_i n_i (q_i  - q_target)  = 0.
```

Monthly constraints use month-specific counts `n_im`; annual-total constraints
are defined separately. Calendar-class conditioning is therefore part of the
weighting contract, not only a date-rendering concern.

## Constructive fixture

The six-block fixture contains symmetric extreme, intermediate, and central
annual means with different within-year variances. Reweighting the library
preserves its daily first and second moments exactly within binary64 fixture
tolerance while moving variance from within-year to between-year components.

| Quantity | Baseline | Reweighted | Change |
|---|---:|---:|---:|
| Daily mean | 0 | 0 | 0 |
| Daily second moment / total variance | 4.333333 | 4.333333 | 0 |
| Between-year variance | 1.666667 | 2.333333 | +40% |
| Mean within-year variance | 2.666667 | 2.000000 | −25% |
| Physical daily values modified | 0 | 0 | 0 |

This is an existence proof only. It does not establish that all 12 monthly
precipitation/temperature surfaces, occurrence/transition cells, cross-variable
moments, and Gate 1 components have a common feasible weight vector at every
station.

## Dependence and low-frequency behavior

For a stationary weight vector `pi`, the fixture uses

```text
P_ij = rho * I(i = j) + (1 - rho) * pi_j.
```

It satisfies `pi P = pi`. For a centered annual state value `f`, its lag-one
covariance is exactly

```text
Cov(f_t, f_(t+1)) = rho * Var_pi(f).
```

At `rho = 0.6`, the fixture's computed and analytical lag-one covariances are
1.4 to floating-point tolerance. More generally,

```text
P^k = rho^k I + (1 - rho^k) 1 pi
gamma(k) = rho^k Var_pi(f).
```

The zero-frequency spectral density relative to an independent sequence with
the same marginal variance is `(1 + rho) / (1 - rho)`, equal to 4 for the
fixture. Thus this particular reset kernel increases low-frequency power
without changing the stationary one-year distribution. This is consistent
with the block/state-conditioning direction identified in the accepted report
and the Steinschneider–Brown literature.

The same kernel is unusable as written: its stationary same-block repeat
probability is 0.6777778. Moving from individual blocks to state classes and
selecting a different block within state may reduce repeats, but exclusion
changes the conditional kernel. A no-duplicate weighted permutation removes
replacement but also removes the simple stationary proof. Neither alternative
has a pinned bounded algorithm yet.

## Structural counterexample

If every selectable block has the same within-year variance `c`, then

```text
daily second moment = annual mean squared + c.
```

Holding the daily second moment and annual mean fixed therefore fixes weighted
annual mean-squared and between-year variance. No reweighting can improve annual
dispersion. This proves that whole-year preservation by itself does not make a
candidate gate-feasible; actual faithful libraries must be solved and audited.

## Finite-horizon and calendar obligations

An implementation contract still has to determine:

- fixed pool/chunk size and the maximum cost relative to a 100-year run;
- whether selection is with replacement, without replacement, or state-level;
- a numeric exact-block reuse ceiling;
- initialization and boundary behavior for the common 30-year prefix of the
  100-year trajectory;
- how 365- and 366-day blocks are matched to target calendar years without
  changing physical values or breaking typed Gregorian output;
- bounded deterministic behavior when no path satisfies all prefix constraints;
- whether monthly preservation is stationary, expected, or an enforceable
  finite-prefix invariant.

None may be left to an unbounded retry or to post-generation selection using
confirmation metrics.

## Development evidence and limitations

A5b provides exposed station and climate diagnostics, not retained faithful
daily base trajectories; the shared-base archive contains runspecs and
provenance only. Reconstructing and optimizing a selector over actual faithful
year libraries would create a development candidate, which is permitted but
requires a separately pinned solver, constraints, and result schema. That
executable development step does not exist in this package and cannot be
replaced by the six-block existence proof.

The analysis also does not claim that EOF, VAR, HMM, or spectral families are
incapable. Fourier/EOF remains a reasonable state representation; A5d rejects
using it as an unconstrained daily multiplier.

## Verdict and first follow-on action

Verdict: `HOLD-CONTRACT-INCOMPLETE`.

The first follow-on action is a development-only solver package that:

1. regenerates hash-bound faithful-off year libraries for the exposed 17
   stations;
2. solves the complete registered monthly/daily constraint system while
   maximizing the complete annual target vector, not only spectral power;
3. implements and compares bounded repeat-safe path constructions at fixed
   pool sizes;
4. proves common-prefix and calendar-class behavior; and
5. closes `STRUCTURALLY-FEASIBLE` only if the solution exists across all
   development stations without reading any confirmation target.

Until then, no station-model ID, profile ID, or coefficient grammar is frozen.

## References

- Chen, J., Brissette, F. P., & Leconte, R. (2010). *Journal of Hydrology*,
  388, 480–490. [DOI 10.1016/j.jhydrol.2010.05.032](https://doi.org/10.1016/j.jhydrol.2010.05.032).
- Steinschneider, S., & Brown, C. (2013). *Water Resources Research*, 49,
  7205–7220. [DOI 10.1002/wrcr.20528](https://doi.org/10.1002/wrcr.20528).
- Wilks, D. S., & Wilby, R. L. (1999). *Progress in Physical Geography*,
  23(3), 329–357. [DOI 10.1177/030913339902300302](https://doi.org/10.1177/030913339902300302).
