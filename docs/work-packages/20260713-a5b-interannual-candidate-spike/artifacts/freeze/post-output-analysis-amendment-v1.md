# A5b Post-Output Analysis Amendment v1

Date: 2026-07-13
Status: **FROZEN BEFORE CLIMATE OR WEPP ANALYSIS OUTPUT**

## Boundary and disclosure

The complete climate and WEPP evidence campaigns are sealed. The post-WEPP
candidate manifest has SHA-256
`6c74128a2d1a3017834474f858fb2ceebe52d5bbe2b39fb3dada953c8440cd06`,
and all 1,904 transient candidate CLI files have been removed. No climate gate
row, candidate metric, candidate aggregate, candidate comparison, WEPP
comparison, or promotion result was viewed before this amendment.

The pre-candidate climate analyzer `artifacts/climate/analyze-a5b.py` remains
immutable. Its first production invocation failed closed before writing
`a5b-analysis-v1.json`. Consequently, the downstream WEPP analyzer was not
invoked and `a5b-wepp-analysis-v1.json` was also absent.

The package already carries the separate candidate-response inspection
disclosure from post-climate amendment v2, so all eventual downstream results
remain exploratory for model-selection purposes. This amendment introduces no
new response-value inspection.

## Failure and cause

The original analyzer reported:

`The truth value of an array with more than one element is ambiguous. Use a.any() or a.all()`

A traceback-only rerun, without opening any analysis result, located the
failure at `conventional_median(candidate_by_station[item].families[family])`.
That value is a NumPy array. `conventional_median` used `if not values`, which
is valid for ordinary Python sequences but undefined for a multi-element
NumPy array. The adjacent `nearest_rank` helper used the same latent emptiness
predicate and would fail on an array at a later stage.

## Corrected analyzers

`artifacts/climate/analyze-a5b-v2.py` is an independent successor. It changes
only the two emptiness tests:

- `conventional_median`: `if not values` becomes `if len(values) == 0`;
- `nearest_rank`: `if not values` becomes `if len(values) == 0`.

Sorting, conversion to `float`, median arithmetic, nearest-rank arithmetic,
eligibility, denominators, gates, thresholds, bootstrap settings, matrix
membership, and output paths are unchanged. The self-test adds positive
NumPy-array vectors for both functions. Production output binds both the
immutable pre-candidate analyzer identity and the corrected analyzer/freeze
identities.

`artifacts/wepp/analyze-wepp-v8.py` independently succeeds the immutable v7
analyzer. It changes no WEPP response parsing, aggregation, matrix, metric,
gate, or campaign rule. It binds the corrected climate analyzer and requires
the climate analysis to carry the original analyzer, corrected analyzer, and
post-output freeze identities before it revalidates all 2,176 WEPP records.

Both corrected analyzers must pass static checks and complete self-tests
before production analysis. Production must begin with both analysis output
paths absent and must refuse to overwrite either output.
