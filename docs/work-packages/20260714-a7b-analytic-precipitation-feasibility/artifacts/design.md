# A7b Design and Interpretation Boundary

Status: frozen before candidate-specific A7b output
Date: 2026-07-14

## Question

Can either of two compact daily precipitation kernels represent the A7a
spell/occurrence priority while preserving the existing monthly wet fraction
and monthly-total variance budget through explicit moment reallocation, with a
fit and RNG design bounded enough for one A7c integration pilot?

## Candidate isolation

The candidates differ only in occurrence state:

1. `o2_logqspline_gaussian_copula_v1` uses the four pair states DD, DW, WD,
   and WW and one wet probability for each state.
2. `sm2_logqspline_gaussian_copula_v1` uses D1, D2+, W1, and W2+ states. Each
   dry/wet spell has one continuation probability after its first day and one
   geometric-tail continuation probability from age two onward.

Each station-season shape is fit from Daymet R1mm occurrence with Jeffreys
0.5 pseudocounts. For a legacy station month, a single declared logit shift
recenters all second-order probabilities, or applies opposite shifts to wet
and dry semi-Markov continuation probabilities, until the four-state kernel's
stationary wet fraction equals
`P(W|D) / (1 - P(W|W) + P(W|D))`. Monthly probabilities must remain inside the
frozen guard. The state carries across month boundaries in a future pilot;
stationarity is certified for each frozen monthly kernel in isolation, and
boundary transients remain an A7c evaluation target.

## Wet-amount marginal and persistence

Both occurrence candidates share one amount model so selection isolates
occurrence structure. Each station-season stores observed positive-amount
knots at probabilities 0, .01, .05, .10, .25, .50, .75, .90, .95, .99, and
1. In log amount, linear interpolation defines `z(u)`. For dispersion
parameter lambda, the dimensionless positive quantile is

`Q_lambda(u) = exp(lambda*z(u)) / integral(exp(lambda*z(v)), v=0..1)`.

Multiplication by the legacy wet-day mean preserves that mean exactly. A first
root `lambda_legacy` matches the legacy wet-day variance. A second root no
greater than `lambda_legacy` reduces, but never increases, that variance until
the candidate monthly-total variance equals the legacy first-order/independent-
amount budget. The retained wet-amount variance fraction and p95/p99 normalized
tail error are explicit gates.

Seasonal adjacent-wet-day Spearman correlation maps to a Gaussian-copula
correlation by `rho = 2*sin(pi*Spearman/6)`. The amount copula persists only
within an uninterrupted wet spell and resets after a dry day. Fixed
Gauss--Legendre and Gauss--Hermite quadrature calculate marginal and bivariate
moments; no random candidate time series is generated in A7b.

## Monthly-total budget

For monthly length `n`, stationary wet fraction `mu`, wet amount mean `m`,
occurrence endpoint probability `P(I_t=1,I_{t+h}=1)`, uninterrupted-wet
probability `P(I_t=...=I_{t+h}=1)`, wet-amount variance `v`, and within-spell
amount covariance `c_h`, the certified variance is

`m^2 * [n*mu*(1-mu) + 2*sum((n-h)*(P_end(h)-mu^2))]`

`+ n*mu*v + 2*sum((n-h)*P_all_wet(h)*c_h)`.

The target uses the legacy first-order occurrence kernel and independent wet
amounts with the exact f32-widened legacy mean and standard deviation. If the
candidate occurrence term alone exceeds that target, or matching the target
would require wet-amount variance greater than the legacy variance, the cell
is infeasible. This is variance reallocation, not variance addition.

## RNG and integration boundary

A future A7c runtime owns two domain-separated streams and consumes exactly
one occurrence uniform and one amount normal/uniform source value per calendar
day, even on dry days. Occurrence state and the amount-copula state are profile-
owned. No draw depends on rejection, wet-day count, path selection, or output
repair. A7b certifies this ownership statically; it does not implement it.

## Selection restraint

The dry/cold/wet A7c development stations must have all 36 month cells
feasible. At least the frozen corpus breadth must also be feasible. Qualifying
candidates are ranked by development breadth, corpus breadth, median
station-level in-sample occurrence log-loss improvement over the legacy
first-order kernel, median retained wet-amount variance, median tail error,
and identifier. In-sample likelihood is a deterministic tie-break, not
confirmation. A selected mechanism is authorized only for a separately frozen
three-station pilot; feasibility does not predict climate improvement.
