# A8c consolidated review

Verdict: **ACCEPT — STOP TERMINAL**

Date: 2026-07-15

## Review boundary

This review covers the revision-2 routed station interface, explicit
`a8c_routed_daily_v1` profile, integrated and fallback runtime paths, frozen
six-station campaign, result artifacts, and closure disposition. Faithful
CLIGEN behavior remains governed by ADR-0001 and the vendored Fortran. The
review does not treat a successful implementation as evidence that the
candidate climate model should advance.

## Contract and evidence checks

- The prospective contract fixes six stations, two explicit routes, four burn
  offsets, nested 30/100-year horizons, Daymet comparison, monthly targets,
  storm/winter guards, and a two-terminal rule before candidate generation.
- The pre-generation freeze binds 40 files. The only pre-outcome amendment was
  triggered by an absent cached `budget` object in three infeasible A8a
  fallback cells. The failed invocation wrote no result. The amendment derives
  the same A7b legacy variance identity from retained `pww`, `pwd`, wet mean,
  wet SD, and days; all reported parent targets agree with the reconstruction
  to `1e-12`. No threshold or candidate byte changed.
- The matrix ran 96 processes and retained 24 candidate/faithful station-burn
  pairs. Every candidate replay and 30-year row prefix passed. The fallback
  route was row-identical to faithful in all four burns.
- The deterministic LFS archive contains the exact 96 retained `.cli` and
  provenance files (27,481,991 bytes compressed), each checked against the
  execution manifest. The restore utility validates archive and member hashes
  before writing under `target/`.
- Final independent analysis replay and identity verification passed 160
  checks and reproduced `STOP-A8-ROUTED-DAILY` byte-for-byte.
- The first full gate run caught a stale runtime copy of the expanded
  provenance schema. The public schema was copied to the required runtime
  mirror, and an A8c quality-report round-trip test was added. This was an
  output-validation correction after the climate decision; it did not alter
  generation, evidence streams, metrics, or the stop terminal.

## Implementation review

The extension is explicit and fail closed. Revision-1 documents and legacy
`.par` inputs cannot select A8c; revision-2 routed documents cannot enter an
older profile. Integrated and fallback model/route/fit/hash combinations are
closed, and the provenance validator requires the corresponding exact fit ID.
The profile is continuous-only, interpolation-none, faithful-QC, and
non-default.

Faithful precipitation still calls the unchanged `gen_precip`. The fallback
variant owns no extension state and delegates to that same function. The
integrated path owns two domain-separated SplitMix64 streams, consumes one
open-interval draw from each per calendar day, initializes history to `DD`,
and carries occurrence and amount state across month/year boundaries. Its f64
transcendentals use `libm`; the faithful f32 path remains unchanged. Unit tests
pin draw counts, repeatability, inverse-normal values, and normalization.

The faithful public `clgen` entry remains a wrapper over the routed internal
seam, and the existing `generation_setup_with_profile` return type is
preserved. Full repository tests retain faithful `.cli` goldens. No fast-math,
reference-tree edit, silent default, or legacy precision change was found.

## Scientific result

The registered daily objectives succeeded:

| Family | 30-year median improvement | 100-year median improvement | Nonworse stations |
|---|---:|---:|---:|
| Spell structure | 0.251 | 0.207 | 5/6 at each horizon |
| Higher-order occurrence | 0.476 | 0.469 | 5/6 at each horizon |

That result is insufficient for continuation. Wet-amount mean passed only
47/72 station-month cells at 30 years and 36/72 at 100 years. Bakersfield July
had no precipitation under either route/horizon, so wet-amount mean and total
mean/variance were unavailable. The largest 100-year wet-amount relative
errors were Bakersfield August (1.206) and Phoenix June (0.912).

All finite/bounds and cold-wet normalized-peak checks passed across 5,941 cold
wet candidate rows. The storm guard failed because every integrated station's
time-to-peak median was zero while faithful medians were positive. The exact
cross-variable guard also failed: Boise dew point differed on 20,675 pooled
rows and Alamosa wind speed on 29,670; other guarded fields remained exact.
This is consistent with existing CLIGEN wet/dry-conditioned downstream paths,
so it is a model-structure consequence of replacing occurrence rather than
evidence of RNG desynchronization.

## Findings

No open P1 or P2 finding remains.

- P3 — The pilot contract's exact cross-variable guard was intentionally
  conservative but not structurally neutral: precipitation occurrence is an
  input to selected legacy dew-point and wind paths. The stop remains valid;
  any future mechanism must model and evaluate those couplings prospectively.
- P3 — Full serialized stream hashes include lexical runspec paths and are
  therefore execution-environment evidence. The climate-row hashes, exact
  archive, input hashes, and deterministic scripts preserve the scientific
  and local replay claims; no cross-host whole-file identity claim is made.
- P3 — The stopped profile remains implemented solely as an explicit
  experimental development surface. It is not recommended for production,
  is not the default, and does not authorize an A8d package.

## Disposition

`EXECUTED-COMPLETE` with terminal `STOP-A8-ROUTED-DAILY` is supported. No
confirmation, retuning, gate relaxation, WEPP response campaign, or promotion
follows. A new precipitation proposal would require operator roadmapping and a
fresh prospective contract that jointly treats wet-amount calibration,
storm time-to-peak, and precipitation-conditioned downstream variables.
