# A5d Experimental Candidate Contract Disposition

Status: `EXECUTED-HOLD-CONTRACT-INCOMPLETE`
Public compatibility status: unchanged

## Candidate boundary

The evaluated thesis is a research-only state-conditioned complete-year/block
selector. Fourier/EOF coefficients describe annual state; they do not multiply
or otherwise mutate daily precipitation, temperature, radiation, wind,
dewpoint, or storm values. A faithful QC-off generator supplies a deterministic
block library under a separate seed domain.

No public candidate ID is pinned. Reserving a station-model or generation-
profile ID would imply more stability than the current contract supports. Any
follow-on remains outside accepted station-document, runspec, generation-
profile, provenance, typed-output, and legacy `.par` surfaces.

## Contract elements that are ready to retain

- Base behavior: `faithful_5_32_3 + qc_filter: off`.
- State representation: finite f64 annual/monthly features compressed through
  a pinned real Fourier basis and deterministic EOF convention.
- Variance posture: constrained reallocation under daily/monthly first- and
  second-moment and occurrence/dependence guards; no multiplicative overlay.
- Physical preservation: selected daily/storm values remain bitwise unchanged;
  new physical-value intervention target is zero.
- Lineage: experimental record binds base pool, coefficients, state features,
  weights, transition/path, selected block indices, seeds, diagnostics, and
  published output hashes.
- Compatibility: all model/profile/schema axes remain independent; research
  artifacts do not enter accepted public enums.

## Proposed coefficient payload

A development schema may include, with independent grammar and model versions:

- exact annual feature membership, ordering, units, and normalization;
- Fourier basis identity, EOF loadings/eigenvalues, retained-rank rule, and
  hierarchical/regional pooling coefficients;
- library-year sufficient statistics used by the feasibility constraints;
- target stationary weights and their solver certificate;
- state classes or transition parameters;
- monthly mean/second-moment, wet-frequency, transition, temperature-order,
  daily precipitation, and descriptor constraint bounds;
- pool/chunk, calendar-class, reuse, and finite-prefix settings.

The payload must use finite f64 coefficient-science values and canonical strict
JSON. This does not authorize f64 changes inside faithful generation.

## Unresolved selector contract

The existence fixture's kernel

```text
P_ij = rho I(i=j) + (1-rho) pi_j
```

is stationary and creates the intended lag covariance, but repeats an exact
block with probability 0.6778 at the fixture's `rho = 0.6`. Three possible
production shapes remain mutually incompatible until evaluated:

1. **With replacement:** retains the stationary proof but repeats exact daily
   years and needs a reuse guard.
2. **Without replacement / weighted permutation:** eliminates duplicates but
   loses the simple stationary distribution and changes finite-prefix
   marginals through depletion.
3. **State-level persistence with conditional block selection:** reduces exact
   repeats but exclusion and calendar matching alter the conditional kernel;
   stationarity and reuse bounds require a new proof.

The package cannot choose among these after inspecting confirmation behavior.
A bounded development solver must make the choice before any ID is frozen.

## Missing executable decisions

- Fixed library/chunk size and acceptable generation cost.
- Exact constraint system, tolerance, solver, pivot/tie rules, and infeasibility
  certificate.
- Transition/path algorithm and a finite iteration bound.
- Initialization and 30-/100-year common-prefix construction.
- 365-/366-day source/target matching and date relabeling.
- Exact-block reuse ceiling and treatment of non-immediate duplicates.
- Domain-separated pool/selector RNG algorithms and byte-level labels.
- Canonical output ordering and proof of unchanged physical daily fields.
- Failure behavior when a station, horizon, or prefix has no feasible path.

## Development fixture requirements

A follow-on contract must add positive and adversarial vectors for:

- feasible and infeasible station constraint systems;
- solver certificate replay and coefficient tampering;
- stationary weights and finite-prefix deviations;
- repeat/reuse and calendar-class exhaustion;
- common-prefix identity at 30/100 years;
- identical selected physical values and changed date/index fields only;
- seed-domain separation and deterministic replay;
- bounded solver/path failure;
- provenance and selected-index content hashes.

## Disposition and first follow-on action

Disposition: `HOLD-CONTRACT-INCOMPLETE`.

The first action is to implement a research-only constrained-weight and
repeat-safe path prototype against regenerated A5a/A5b development libraries.
It must emit solver certificates and invariant diagnostics without producing or
reading confirmation metrics. Only a cross-station feasible result may proceed
to a frozen experimental schema and IDs.
