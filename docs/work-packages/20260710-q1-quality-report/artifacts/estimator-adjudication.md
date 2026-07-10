# Estimator Adjudication — Q1 Stage S

Date: 2026-07-10
Author: Claude Code (Stage S)
Evidence mode: labeled per item (Ran = executed this session;
Static = source reading with citations).

## 1. Group A targets: as-parsed vs post-correction `.par` values

**Ruling: targets are the parsed `.par` values plus exactly the
corrections the source applies to a parameter before using it —
"the target is what the generator was asked to reproduce"
(SPEC-QUALITY-REPORT group A) — mapped to the `.cli` consumer-surface
units.**

Evidence (Static, `sta_parms` cligen.f:2793-2815 via
`crates/cligen/src/par/sta_parms.rs`): `rst`, `prw`, `obmx`, `obmn`,
`stdtx`, `stdtm`, `obsl`, and the dew-point row (`rh`) are distributed
into generation state **verbatim**. The load-time derivations (`wi`
halving, CV computation, cumulative wind-direction distribution) do
not alter any group A parameter's target surface.

Per parameter:

| Parameter | Target | Basis |
|---|---|---|
| precip wet-day mean / SD | `rst(m,1)`/`rst(m,2)` × 25.4 (in → mm) | distributed verbatim; the `.cli` surface is mm |
| precip wet-day skew | `rst(m,3)` **clamped to ±4.5, then 0.0 → 0.01** | the source mutates the station skew in place before every use (`gen_precip`, cligen.f:1237-1238) and replaces a zero skew with 0.01 (cligen.f:1244-1246). New Meadows August SKEW P = 4.82 → effective target 4.5. Skew is scale-invariant, so no unit mapping. |
| P(W\|W), P(W\|D) | `prw(m,1)`, `prw(m,2)` as parsed | distributed verbatim |
| wet-day fraction | P(W\|D) / (1 − P(W\|W) + P(W\|D)) | the source's own stationary-Markov expectation — the header `smy` formula (cligen.f:3741-3745) and `r5monb`'s expected-wet-days formula use exactly this |
| tmax / tmin mean | (`obmx`/`obmn` − 32) × 5/9 | verbatim °F values; the `.cli` surface is °C |
| tmax / tmin SD | `stdtx`/`stdtm` × 5/9 | SD is translation-invariant; only the scale maps |
| radiation mean | `obsl` as parsed | already Langleys/day on both surfaces |
| dew-point mean | (`rh` − 32) × 5/9 | the DEW PT record is °F |
| wind-speed mean | Σ_dir (pct/100) × mean_dir over the 16 directions | `windg` draws a direction from the cumulative `wvl` percentage distribution and a speed from that direction's statistics; a uniform beyond the summed percentages is a calm day with `wv = 0` (cligen.f:2020-2119) — so the asked-for mean weights direction means by probability with calm as zero |

Not treated as target corrections (they are generator behavior the
report should *price*, not bake into the target): the wet-day 0.01 in
floor (cligen.f:1259), the daily radiation clamp to
[0.05·rmx, rmx] (cligen.f:1500-1505), the negative wind-speed 0.1
floor (cligen.f:2113), and the per-direction zero-skew 0.01 guard.

f32 → f64: parsed `.par` fields widen to f64 before target
arithmetic; all estimator accumulation is f64 (spec §Determinism).

Interpolation caveat (on the record): with `-I1..3` the generator's
effective daily parameters differ from the monthly values; the report
keeps the monthly `.par`-derived targets, so group A on interpolated
runs includes the interpolation-method bias. The mt-wilson/fish-springs
goldens (`-I2`) measure cleanly under this rule.

## 2. Parser reuse: `cli_diff` vs dedicated intake

**Ruling: dedicated intake (`quality::intake`), not a reuse of
`cli_diff`'s parser.**

- `cli_diff`'s contract (SPEC-CLI-DIFF) is exact-token comparison: it
  retains field **lexemes** as strings, validates numerics only to
  fail closed, and exposes no parsed-value surface. The quality
  instrument consumes **numeric values** (f64).
- Coupling them would either push a value-typed representation into
  the differ (whose identity gates depend on token semantics) or
  force the quality module through string re-parses of a borrowed
  representation. Both parsers are small; the shared truth is the
  13-field daily-row shape, which SPEC-CLI-DIFF §Semantics already
  pins as the normative table and both cite.
- The intake adds two quality-specific obligations the differ has no
  use for: finiteness rejection (a `NaN`/`inf` token parses as f64
  but must fail closed here) and strictly-increasing dates (decade
  blocking and Markov transitions depend on chronological rows).
- A future SPEC-CLI-TEXT could give both a common substrate; that is
  a registry-planned spec, not this package.

## 3. Estimator pins as implemented (`quality::estimators`)

| Estimator | Pin |
|---|---|
| mean | f64 sum in row order / n; null on empty |
| SD | n−1 sample convention; null for n < 2 |
| CV | sd/mean, sign follows the mean; null when mean = 0 |
| skew | adjusted Fisher–Pearson g1·√(n(n−1))/(n−2); null for n < 3 or zero variance. Ran: matches the hand-derived reference 1.6970562748477141 for [1,2,3,4,10] (verified against an independent Python computation this session, 1.6970562748477143 — within 2 ULP of the Rust value; test tolerance 1e-12) |
| Pearson | two-pass centered sums; null for n < 2 or zero variance |
| Spearman | average-rank ties (tied values share the mean of the ranks they span), then Pearson over ranks |
| top-N events | depth descending; ties break by earlier date, then lower (1-based) row index |
| decades | fixed 10-year blocks from the first row's year (`decade` is the 0-based block index; `start_year = first_year + 10·decade`); trailing partial block carries its `n_years` = distinct years present |
| Markov transitions | consecutive row pairs (the WEPP table is contiguous daily by contract, enforced by the strictly-increasing-date intake), attributed to the second day's month; a scope's first row has no predecessor within that scope |
| error cells | `abs_err = \|generated − target\|`; `rel_err = abs_err / \|target\|`, null when target = 0. Sign is recoverable: both `target` and `generated` are in the cell |
| annual statistics | every parsed year contributes; partial years (observed truncation) are visible via group D `per_year.n_days` and monthly cells carry their own `n_years` |
| year-boundary spells | group D wet/dry spells are clipped at year boundaries (per-year computation) |
| JSON | serde struct order = schema order; pretty 2-space; trailing newline; every value finite-or-null (NaN can never be emitted); `float_roundtrip` feature pinned so consumers parse the exact emitted f64 |

## 4. Non-finite parse hazard (found and closed in Stage S)

Ran: `serde_json`'s default f64 **parse** is best-effort (±1 ULP);
the round-trip test caught `0.22016381100650317` re-parsing as
`...315`. Emission was never affected (Ryu shortest-round-trip), but
consumer-side exactness is part of byte determinism, so the
`float_roundtrip` feature is pinned in `Cargo.toml` with a comment.
