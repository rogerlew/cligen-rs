# A11 revision-1 design freeze

Status: **ratified prospectively before candidate output**

Science contract: `a11-forced-monthly-annual-oracle-science-v1`

Candidate count: one

The machine authority is `design-freeze-v1.json`. It freezes the six existing
A10 temporal sites, candidate-fit-only regional variation fitting, immutable
PRISM containing-cell climatology, eight nested 100-year streams, the existing
A10 temporal metric/scoring surface, and the A5 WEPP response protocol.

No fit-validation target value enters forcing or structure fitting. The only
site-specific candidate input is the previously captured transferable PRISM
normal vector. Every variation and daily-texture quantity is explicitly
region-pooled from the 1,200 `candidate_fit` Daymet objects.

The joint target law is a single 48-dimensional empirical Gaussian copula.
Its four monthly blocks are precipitation total, wet fraction, mean
temperature, and positive mean diurnal range. Because all blocks are fitted
and projected jointly, requested and effective cross-block dependence are
reported together. Marginal climatological transforms use PRISM directly;
they do not read development observations. Requested annual dispersion is the
dispersion implied by the same complete candidate-fit annual rows, so the
monthly/annual covariance identity is coherent by construction. The receipt
still reports the eigenspectrum adjustment and requested/effective values.

The daily law has no retry or repair path. It samples an exact-count Markov
bridge, normalizes one positive amount-weight vector once, centers/scales one
temperature-residual vector once, and scales one positive range vector once.
Those are the registered conditional transforms.

The local checkout has compact prior WEPP evidence but not the exact native
executable and scenario materialization required to install a new candidate
climate stream. WEPP remains mandatory. Its absence cannot become a pass and
does not authorize confirmation. The candidate climate experiment is still
run because it answers the frozen climate hypothesis and distinguishes a
climate failure from the already-known execution-surface absence.
