# `wepppy` PRISM localization sanity review

Date: 2026-07-18
Evidence mode: static source review

## Reviewed identity

- repository: `/Users/roger/src/wepppy`
- commit: `3ee74d02df445a30968ef92975e5e3e2f6084669`
- `wepppy/climates/cligen/cligen.py` SHA-256:
  `4071cc72165d174851316349c0d96a3f4fa06fcf0b2d91e5b67de439f39a42c1`
- `wepppy/climates/metquery_client.py` SHA-256:
  `f7a15ea0d331800467668252f3ae2e1204c3f28f2a9549caaef3986177bb9fc4`
- `wepppy/climates/prism/__init__.py` SHA-256:
  `0d997d37cdf6d9d691b09c3796c6b5465836d150d87724beeaf15865d4d0672a`

The relevant implementation is the US station heuristic at `cligen.py`
1864--1923, `par_mod` at 2535--2830, monthly metquery accessors at
`metquery_client.py` 153--200, and the faithful CLIGEN intensity authority in
this repository's `reference/cligen532/cligen.f` (`alph`, `r5monb`, and the
record-15 read/load-time halving).

## What the code actually does

The current US selector takes the nearest ten stations, starts every candidate
with its distance rank, and adds latitude rank (weight 1), elevation rank
(weight 1), and PRISM precipitation-normal rank (weight 3). It does not use
Tmax or Tmin normals. Target elevation comes from a separate live elevation
query. The EU/Australia selectors add Tmax and Tmin ranks at weight 1.5 each.

`par_mod` obtains monthly PRISM ppt/Tmax/Tmin from the WEPPcloud metquery
proxy, derives the station wet fraction as
`pwd / (1 - pww + pwd)`, moves wet-day count halfway toward the PRISM/station
monthly precipitation ratio within bounds, preserves `pwd/pww` while solving
new transition probabilities, replaces mean wet-day precipitation and
temperature means, and optionally scales raw `MX .5 P` by the monthly
precipitation ratio clamped to 0.5--2.0. It then invokes CLIGEN.

## Sound parts adopted

- The stationary wet-fraction equation is correct for the two-state Markov
  chain.
- The transition formulas correctly preserve `pwd/pww` while attaining the
  requested stationary wet fraction when inputs are strictly interior.
- The halfway wet-day response, 50--200% station bounds, 0.1-day lower bound,
  `D - 0.25` upper bound, 0.05-inch dry threshold, and 0.5--2.0 intensity
  clamp form a bounded, reproducible heuristic. They are acceptable for this
  comparator when named as heuristic rather than calibration truth.
- Replacing `.par` records 4, 7, 8, 9, 10, and 15 leaves the remaining CLIGEN
  structure station-derived and makes the downstream generator genuinely
  faithful to the localized file.
- `MX .5 P` is raw inches/hour in the file and is halved to maximum half-hour
  depth during faithful load. Scaling record 15 is therefore the correct
  lexical surface for the requested intensity adjustment.

## Corrections required before reuse

1. The metquery calls are unversioned live HTTP requests with no timeout,
   response/content hash, PRISM release identity, cell receipt, or access
   provenance. Revision 1 instead queries verified local official rasters.
2. The US selector does not match the operator's frozen distance/latitude/all-
   normals axes. The new selector explicitly uses ppt/Tmax/Tmin ranks and no
   unrequested elevation service. It retains the rank-sum form and the
   all-normal weights already present in `wepppy`'s EU/Australia path.
3. Candidate and final ties rely partly on stable input order. The new
   selector makes station ID an explicit component and final tie-break.
4. `get_station_fromid` uses substring matching. The new mode selects an
   exact catalog row and exact path.
5. `_row_formatter` branches on `v < 1.0`; for a negative temperature it
   removes the first character of the formatted value, which is the minus
   sign. The new implementation must use SPEC-PAR's signed fixed-width
   renderer and regression vectors with negative temperatures.
6. `par_mod` silently floors PRISM monthly precipitation and mean wet-day
   precipitation to 0.01 inch. That can materially bias arid cells after
   multiplication by wet-day count. The new mode records fixed-width
   quantization and fails if a positive target cannot be represented.
7. Derived transition values fall back only on `NaN`; infinity and other
   out-of-domain results are not rejected. Revision 1 requires finite,
   strictly valid inputs and outputs before rendering.
8. The intensity adjustment is optional and defaults off. It is mandatory in
   the new comparator because the operator explicitly included it.
9. The writer emits CRLF literals. cligen-rs SPEC-PAR requires LF records for
   its lexeme-preserving surface, so the new mutation path preserves LF and
   proves untouched-record/tail identity.

## Scientific caveat retained

Scaling `MX .5 P` by the monthly precipitation-total ratio is not based on a
PRISM subdaily-intensity product, and the simultaneous wet-day-frequency
change means it is not the same as scaling by conditional wet-day mean. The
package retains the bounded existing rule for comparator continuity, labels
it as a heuristic, records the factor, and forbids interpreting the result as
observed PRISM intensity. A conditional-intensity alternative requires a new
version and an explicit comparison; it is not silently substituted here.

## Disposition

`ADOPT-WITH-CORRECTIONS`. The occurrence algebra and bounded localization are
fit for a research comparator. Network/data identity, selector axes,
determinism, numeric validation, negative-value rendering, quantization
visibility, line endings, and mandatory intensity behavior must be corrected
as frozen in SPEC-A10-STOCHASTIC-PRISM-COMPARATOR.
