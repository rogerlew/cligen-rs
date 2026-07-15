# A8b frozen design

## Question and alternatives

A8b asks one narrow question after accepting A8a unchanged: should an explicit
`legacy_daily_fallback` station remain legacy-only, or can a single bounded
year-state mechanism add cross-month year-to-year structure without changing
the declared monthly precipitation surface?

The registered alternatives are:

1. `legacy_daily_only_v1`: no secondary state, coefficient, or RNG stream;
   legacy daily occurrence, amount, and storm behavior remains unchanged.
2. `bounded_eof2_copula_ar1_reallocation_v1`: two pooled EOF modes drive only
   the conditional mean and residual variance of wet-day precipitation amount.
   Wet/dry occurrence and storm machinery remain legacy.

There is no third candidate and no post-result repair. Failure of alternative
2 selects alternative 1; it does not open another search.

## Corpus boundary

The corpus is exactly the ten A8a fallback stations, split by the already
exposed A8a roles: five development and five confirmation. Daily precipitation
comes from the immutable A8a/A5a Daymet archives already used by A8a. Training
is 1980--2009 and validation is 2010--2025. A8b adds no source, station,
substitution, or classification.

For station `s`, annual monthly precipitation totals form matrix `Y_s` with
years as rows and calendar months as columns. Training columns are centered
and divided by their training sample standard deviations. The standardized
matrices are pooled by rows; station boundaries are retained for lag pairs.

## Shared two-mode state

Let `R` be the pooled 12 by 12 sample covariance of standardized training
totals. The registered shrinkage is

`R* = (1 - lambda) R + lambda I`, with `lambda = 0.25`.

The two largest deterministic-sign eigenvectors and eigenvalues define

`H = E_2 diag(sqrt(lambda_1), sqrt(lambda_2))`.

The state has two independent stationary Gaussian AR(1) coordinates `z_k`.
Each coordinate is mapped without rejection to a bounded, unit-variance state:

`u_k = sqrt(3) [2 Phi(z_k) - 1]`, so `u_k` lies in `[-sqrt(3), sqrt(3)]`,
has mean zero and variance one. Pooled training lag-one Spearman correlation of
each EOF score is mapped to latent Gaussian correlation
`rho_k = 2 sin(pi r_s,k / 6)` and bounded to `[-0.8, 0.8]`. The implied
bounded-state lag correlation is recorded and evaluated on the held-out
period.

The future implementation contract owns a dedicated namespace
`cligen.extension.a8b.precipitation.year_state.v1`, two independent normal
initial-state draws, and two independent normal innovation draws per simulated
year. There is no rejection, retry, count selection, or output-conditioned
branch.

## Exact monthly reallocation

For one station/month, let legacy wet-day count `N` have mean `n`, variance
`v_N`, and second moment `e2_N = v_N + n^2`. Let wet-day amount have legacy
mean `mu` and variance `sigma^2`. The legacy monthly precipitation mean and
variance are

`M0 = n mu`

and

`V0 = n sigma^2 + v_N mu^2`.

The registered first-order Markov wet-count moments use the exact A7b legacy
occurrence equations. Candidate raw total-mean-shift loadings are

`B_raw = sqrt(0.5) diag(sqrt(V0)) H`.

After one station-wide scale `gamma`, bounded year-state total shift is
`D = B u`, where `B = gamma B_raw`. Wet-day mean becomes

`mu(u) = mu + D / n`.

Occurrence is unchanged. The conditional wet-amount variance is the constant

`q = sigma^2 - C_mm e2_N / n^3`, where `C = B B^T`.

The law of total variance then gives exactly

`Var(monthly total) = n q + v_N E[mu(u)^2] + Var(D) = V0`.

Thus `C_mm` moves variance from conditional wet amounts into between-year
monthly means; it does not add monthly variance. Monthly wet fraction and mean
also remain unchanged. The scale is 0.95 times the largest value no greater
than one that leaves every active month with at least 25% of its legacy wet-
amount variance and a worst-case wet-amount mean at least 25% of legacy.

A legacy-degenerate month with zero allocable precipitation variance receives
exact zero loadings and unchanged residual amount variance. A station requires
at least nine allocated months and `gamma >= 0.10`; other malformed or
nonallocable cases fail closed.

This budget is for monthly precipitation mean and variance. It deliberately
does not claim preservation of the unconditional wet-day amount variance:
shared year means create within-month amount covariance, so that marginal
amount variance is the source from which the monthly-total budget is
reallocated. Storm, tail, winter, and cross-variable effects remain empirical
A8c gates if the candidate is selected.

## Held-out comparison and decision

The validation target is explicitly the secondary-state surface, not the full
daily generator covariance. Validation monthly covariance retains its diagonal
and shrinks off-diagonals by 0.75. The null secondary-state covariance is zero.
The candidate secondary-state covariance is `C`; the full candidate monthly
diagonal remains `V0` by construction.

For each station A8b compares candidate versus null on:

- RMSE over the 66 off-diagonal monthly correlation cells;
- absolute error in the cross-month contribution to annual-total variance;
  and
- pooled lag-one correlation error for the two EOF scores.

Candidate selection requires all station/month analytic gates, at least nine
allocated months at every station, two-mode explained fraction at least 0.20,
at least 5% pooled improvement for both covariance metrics, joint improvement
at six or more of ten stations, and no pooled persistence degradation. Any
failure returns `USE-LEGACY-DAILY-FALLBACK`. A selected result authorizes only
an A8c development pilot; no A8b result is a promotion.
