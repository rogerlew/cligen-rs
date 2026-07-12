# Independent Source/Port/Specification Review

Date: 2026-07-12
Evidence mode: Static
Reviewer: Codex sub-agent `spec_review`, working read-only from the vendored
Fortran, Rust port, and draft specification

## Scope

The review compared `SPEC-FAITHFUL-GENERATION.md` and its package artifacts
against `reference/cligen532/cligen.f`, the owning Rust symbols, and the
recorded identity evidence. It checked generated fields, units, branch/state
transitions, interpolation use, RNG ownership and draw order, QC behavior,
observed substitution, and scope/evidence claims.

## Findings and dispositions

| Finding | Severity | Disposition |
|---|---|---|
| `timpkd(1:12)` was initially described with calendar-month arrays | High | Corrected: it is one station-wide 12-bin CDF; only its unused interpolation setup treats it as a 12-vector |
| latitude and `itype` were absent from the station dependency table | High | Added with radiation and `tymax`/`xmav` dependencies |
| retained `calm(:)` could be read as a live daily parameter | Medium | Corrected: `windg` uses residual directional probability; `calm` has no daily consumer |
| `r5monb` description omitted its fixed non-leap calendar and zero guards | High | Added `nc`/February behavior, `0.0006944` wet-day guard, and `0.001` rain-mean divisor |
| QC prose overgeneralized normal tests | High | Corrected to columns 2, 3, 4, 5, and 8; wind-speed column 7 is K-S-only |
| QC description omitted 20-bin/100-observation threshold, `50.0` limits, and denominators | Medium | Added exact K-S threshold and `g_dimi` versus `g_dimp` rules |
| precipitation-skew clamp was described as applying to the interpolated surface | High | Corrected: only current stored month is mutated; linear adjacent may be unclamped and precomputed Fourier/Yoder-Foster coefficients never see it |
| precipitation amount zero-recovery timing was incomplete | Medium | Corrected: current `v8=0` is used and stored; direct `k5` recovery occurs at the next generated wet amount |
| `dstg` was under-specified | High | Added `xn1`, mixed f32/f64 rejection equation, acceptance rule, persistent batch/cursor, 20-of-30 rollback quirk, and doubled rejection counter |
| `rn1` warm draw appeared live and refill/daily predecessors appeared to share one continuing chain | Medium | Corrected: `rn1` is unread; first refill initializes both surfaces once, then `last_r` and daily `v*` advance separately |
| continuous `timepk` mask mismatch was absent | High | Added: no recovery for `zx=0` on an actual wet day and pre-drawn values can be unused on actual dry days |
| legacy `timpkd` semantic failure behavior was absent | Medium | Added raw-CDF behavior: no monotonicity/range/bin-width validation, bin-12 extrapolation, and upper-only `0.99` clamp; modern schema must define stricter invariants |
| dew-point `< -10°F` diagnostic was described ambiguously | Medium | Corrected as a mode-independent source diagnostic with load-bearing assignment |
| `r5p`/`tymax` were mislabeled as precipitation depth | High | Corrected to source-described peak rainfall rate in mm/h in the spec, parameter map, and Rust glossary |
| observed EOF was described as making no state write | Medium | Corrected: `msim`/`nsim` reset before the failed read; no climate/RNG work follows |
| evidence totals included deprecated standalone-storm cases without disaggregation | Medium | Corrected to 10 in-scope goldens and 189,205 in-scope days, plus two companion-scope cases |
| package authority omitted setup, observed-default, and QC/ACM ranges | Medium | Added using the ratified unit boundaries in `docs/port/fortran-decomposition.md` |
| structural independence was difficult to discover | Low | Added explicit wet/dry independence for radiation, temperature/dew point, and wind |

## Boundary disposition

The faithful legacy station path accepts `timpkd` values syntactically but has
no semantic CDF validator. This package documents the source behavior and does
not add a new malformed-input policy to the frozen faithful profile. The
modern station schema identified by the follow-on artifact must define and
fail closed on monotonicity, range, terminal probability, finite result, and
nonzero landed-bin width.

## Verdict

All High and Medium findings were dispositioned. No generated field, random
stream, or persistent state remains unrepresented. No unresolved source
ambiguity requires a new reference-binary capture. The current specification
is source-consistent and implementation-grade for continuous and hybrid
observed generation within its declared scope.
