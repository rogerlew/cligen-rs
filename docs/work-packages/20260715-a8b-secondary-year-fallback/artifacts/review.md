# A8b consolidated review

Verdict: **ACCEPT**

Review date: 2026-07-15

## Scope and prospective boundary

A8b accepts the complete A8a partition and tests only the fallback-domain
question. The frozen alternative set contains the explicit legacy-only null
and one new pooled two-EOF Gaussian-copula AR(1) precipitation-amount
mechanism. It contains no A5 identifier, scalar-IID state, second optional
candidate, occurrence change, climate generation, production code, public
schema, or promotion action.

Freeze v1 bound the ten parent fallback identities, periods, shared
standardization, EOF rank, variance-reallocation equations, coefficient
bounds, RNG ownership, validation metrics, guards, and terminal priority before
the first A8b annual aggregate or coefficient existed.

The first fit loaded the registered 300 training station-years and 160
validation station-years, then stopped at the frozen station-month
standardization requirement: `ca042713` has zero sample standard deviation for
June totals in 1980--2009. No coefficient, shared EOF, validation metric, or
decision artifact existed. Amendment 001 changes only exception reporting: it
records structured candidate infeasibility and applies the already registered
legacy-only terminal. It does not omit, impute, pool, or repair the zero-scale
cell and cannot select the candidate. Successor freeze v2 binds that reporting
path and the original freeze.

## Accuracy and identity review

The parent check reproduces exactly five development and five confirmation
fallback stations and verifies A8a's `CONTINUE-A8B-DRY-PARTITION` terminal and
all eight parent guards. ADR-0004 and A5f0 identities match; the candidate is a
new bounded pooled structure, not an exact retired version.

An independent source calculation parsed the archived Daymet object for El
Centro (`ca042713`, archive SHA-256
`5a052c0180e0501056fe7b0dadc73b48d6cae70fdedb905edfaf7aad23f7b1bd`).
All 30 June totals from 1980 through 2009 are exactly 0.0 mm, so the sample
standard deviation is exactly zero. The registered per-station standardization
is therefore undefined; this is not a numerical-tolerance edge.

The canonical coefficient artifact has status
`INFEASIBLE-BEFORE-COEFFICIENTS`, a null shared model, zero station
coefficients, and no use authorization. All eight candidate guards are false.
The parent and explicit null are valid, so the frozen priority selects
`legacy_daily_only_v1` and returns `USE-LEGACY-DAILY-FALLBACK`. Independent
verification reproduces the coefficient sentinel, analysis, decision, and
findings bytes exactly and confirms that no `.cli` exists in the package.

## Consistency and public-safety review

The result is consistent with the simplified campaign. A8b does not treat a
candidate-fit failure as a reason to add another mechanism, drop an arid month,
or revisit A8a. It keeps the fallback domain on the legacy daily occurrence,
amount, and storm path with no secondary year-state and no additional RNG.

The result does not reject EOF, AR, or variance-reallocation mechanisms in
general. It rejects only the exact A8b version over the registered whole
fallback corpus. Because fitting stopped before coefficients, A8b makes no
held-out skill, monthly-budget, storm, winter, cross-variable, or downstream
response claim about the candidate.

A8c may now implement the A8a eligible-domain daily construction and an
explicit `legacy_daily_fallback` route. It must not implement or publish the
A8b coefficient sentinel, candidate ID, RNG namespace, or year-state behavior.
Runtime still may not infer aridity or switch paths from generated output.

## Findings and dispositions

No P1 or P2 finding remains open.

| ID | Priority | Observation | Disposition |
|---|---|---|---|
| A8B-REV-001 | P3 | The candidate failed before EOF, coefficient, budget, and held-out gates. | Limit the conclusion to exact fit infeasibility; make no relative-skill or broader model-family claim. |
| A8B-REV-002 | P3 | A different preregistered degenerate-month rule could define another model, but none was part of A8b. | Do not drop or impute June after outcome access and do not open a replacement search. |
| A8B-REV-003 | P3 | The machine artifact retains a coefficient-schema label even though it contains no coefficients. | Treat `fit_status`, empty station list, and `use_authorization: none` as the controlling fields; A8c must not consume it. |
| A8B-REV-004 | P3 | The zero-scale evidence is Daymet-grid evidence for the frozen coordinate, not a universal statement about El Centro observations. | Scope the result to the registered archive and period. |

## Decision

The evidence supports `USE-LEGACY-DAILY-FALLBACK`. The optional candidate is
ineligible, the legacy-only null is certified, no secondary year-to-year
mechanism proceeds, and A8c remains authorized with explicit legacy fallback.
