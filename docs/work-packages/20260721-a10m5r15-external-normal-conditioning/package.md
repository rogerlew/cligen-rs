# A10M5R15 — External-Normal Conditioning

Status: `SCAFFOLDED`
Date: 2026-07-21
Evidence mode: Prospective development comparison
Starting branch and push target: current `main`, push `main`

## Objective

Test whether immutable PRISM Norm91m monthly precipitation, Tmax, and Tmin
normals close A10's diagnosed site-climatological-location deficit. Execute two
matched attribution pairs: the P2-backed E0/E1 pair and the backbone-free
E2C/E2 replacement pair. Preserve the accepted temporal selector,
calendar/missingness rules, confirmation firewall, and research-only scope.

## Scope

Included:

- exact reconstruction of R14 arm B as E0 and a normals-only extension as E1;
- a descriptor-only backbone-free replacement control E2C and the otherwise
  identical normals-conditioned E2 treatment;
- candidate-fit-only normals normalization and mapping fits;
- the accepted six-site, eight-member, nested 30/100-year temporal protocol;
- paired attribution, temporal eligibility, and ADR-0006 runtime evidence;
- one control allocation and one two-L40/two-wave candidate allocation.

Excluded: P3/P4 re-entry, solar, N3/elevation expansion, spatial promotion,
confirmation access, non-CONUS applicability, Rust runtime integration,
production profiles, and any post-output threshold or architecture change.

## Authority

- [ADR-0006](../../decisions/0006-a10-runtime-boundary-expansion.md)
- [ADR-0007](../../decisions/0007-a10-external-normal-conditioning.md)
- [SPEC-A10-EXTERNAL-NORMAL-CONDITIONING](../../specifications/SPEC-A10-EXTERNAL-NORMAL-CONDITIONING.md), revision 1
- [SPEC-A10-CORPUS](../../specifications/SPEC-A10-CORPUS.md)
- [SPEC-A10-STOCHASTIC-PRISM-COMPARATOR](../../specifications/SPEC-A10-STOCHASTIC-PRISM-COMPARATOR.md)
- the authenticated R14R2R2 scientific terminal and exact R14 contracts pinned
  in `artifacts/predecessor-pin.json`

## Frozen hypotheses

- **H-E1:** E1 reduces the bootstrap median regime-ratio upper-90% relative to
  matched E0 by at least the shared strictly positive attribution margin frozen
  from candidate-blind null/control evidence before output.
- **H-E2:** E2 reduces that statistic relative to matched E2C by at least the
  same frozen attribution margin.
- **H-T:** at least one normals-conditioned arm reaches both frozen temporal
  gates at both horizons: upper-90% at most 1.25 and maximum regime ratio at
  most 1.50.
- **H-R:** a normals treatment can advance only when it and its matched control
  have CPU exports and remain below the ADR-0006 30× hard-failure boundary;
  5× or greater remains a standing warning. Every failed arm remains reported.

Attribution and temporal eligibility are separate. Passing H-E1 or H-E2 does
not waive H-T, and temporal eligibility without the matched frozen contrast is
reported as an unattributed result rather than evidence that normals caused
the gain. This package does not adjudicate or revive A10 H4 hierarchical-
pooling claims; its paired contrasts measure measured-site-climatology value.

## Data calendar and missingness preflight

Before resource reservation, the control stage must authenticate all 1,440
A10M1 fit/validation objects and all six temporal sites against
`artifacts/data-preflight-contract.json`.

- source transform:
  `daymet_official_365_v1_to_proleptic_gregorian_daily`;
- normalized axis: proleptic Gregorian daily;
- each 16-year window: 5,844 axis rows, 5,840 observed core rows, 15 adjacent
  annual pairs, and 13 eligible origins;
- February 29 is observed in leap years; December 31 is the structural null;
- masks require `source_observed` plus finite precipitation/Tmax/Tmin, with
  at least 28 eligible days per month;
- every requested coordinate must return one valid containing PRISM cell;
  masked, non-finite, out-of-bounds, duplicate, or missing normals fail closed;
- the 36-field normalizer is derived from the 1,200 `candidate_fit` rows only,
  in ascending UTF-8 point-ID order using per-field f64 Welford population
  statistics (`ddof=0`), then frozen as a canonical little-endian f64 payload
  and hash-pinned before E1/E2 output;
- PRISM f32 ppt remains monthly millimetres and Tmax/Tmin remain degrees C for
  normalization; normalized model values round once to f32, and a zero or
  non-finite scale fails before reservation;
- E0/E2C receive no normals tensor or normal-derived statistic.

## Execution and dispatch

Execution starts from current `origin/main` on branch `main` and pushes only to
`main`. The living execution sequence is `plan.md` and
`../../exec-plans/20260721-a10-external-normal-conditioning.md`.

The scaffold authorizes source implementation and local verification. It does
not itself authorize GPU reservation. Live execution requires publication on
`main`, fresh toolkit authority, exact runtime/source asset authentication,
successful calendar/normals preflight, and an independently accepted
execution-readiness review.

## Resources

- control/materialization: one L40, at most 30 minutes;
- candidate portfolio: one two-L40 allocation, at most 240 minutes, two
  deterministic waves of two isolated child processes;
- recovery: at most five L40-minutes, cleanup only;
- total ceiling: 515 L40-minute-equivalents;
- one attempt per scientific arm; no scientific retry.

Wave 0 is E0/E1 and wave 1 is E2C/E2. Wave placement is operational only and
may not enter initialization, random fields, losses, metrics, or selection.

## Gates

- exact predecessor, specification, PRISM asset, and contract hashes;
- complete calendar/missingness/normals preflight before reservation;
- exact four-arm roster and matched-pair common-random-field checks;
- explicit absence of normals from E0/E2C inputs;
- exact parameter accounting: E0 278,747; E1 279,467; E2C 2,040; E2 2,760;
- candidate-blind attribution calibration with one shared strictly positive
  margin frozen before output;
- 188-component objective coverage and accepted temporal protocol identity;
- two byte-identical selector replays from authenticated evidence;
- ADR-0006 CPU runtime classification for every arm;
- confirmation, solar, spatial, and promotion roles remain sealed;
- `python3 artifacts/verify_scaffold.py`;
- `cargo fmt --check`;
- `cargo clippy --all-targets -- -D warnings`;
- `cargo test`;
- `git diff --check`.

Coverage/CRAP is not triggered because this scaffold changes no production
function under `crates/`.

## Exit criteria

Terminal precedence is evaluated in this order and exactly one terminal is
published:

1. any firewall, role, provenance, or evidence-authentication violation:
   `FAIL-A10M5R15-INVALID-EVIDENCE`;
2. any incomplete arm, non-finite/support failure, missing CPU export, or
   unreconciled execution/cleanup record:
   `HOLD-A10M5R15-ENGINEERING-INCOMPLETE`;
3. `!any_T(runtime_valid(T))`, meaning neither matched pair has both treatment
   and control survive the ADR-0006 runtime gate:
   `HOLD-A10M5R15-RUNTIME-INELIGIBLE`;
4. `any_T(runtime_valid(T) && temporal(T)) && !any_T(full(T))`, meaning at
   least one runtime-valid treatment is temporal but no single such treatment
   also clears its own attribution gate:
   `HOLD-A10M5R15-ATTRIBUTION-NOT-SUPPORTED`;
5. `any_T(runtime_valid(T)) && !any_T(runtime_valid(T) && temporal(T))`, meaning
   no runtime-valid treatment is temporally eligible:
   `HOLD-A10M5R15-NORMAL-CONDITIONING-NOT-SUFFICIENT`;
6. `any_T(full(T))`: `A10M5R15-TEMPORAL-READY`.

For treatment `T` and its matched control `C`, `runtime_valid(T)` is
`runtime(T) != FAIL && runtime(C) != FAIL`, and `full(T)` is
`runtime_valid(T) && temporal(T) && attribution(T,C)` after the global
engineering-completeness branch. Evidence from different treatments may never
be combined to reach READY.

The named outcomes mean:

- `A10M5R15-TEMPORAL-READY`: at least one normals-conditioned arm passes its
  matched calibrated-attribution gate, both temporal gates at both horizons, all hard
  engineering/firewall gates, and the ADR-0006 runtime gate.
- `HOLD-A10M5R15-NORMAL-CONDITIONING-NOT-SUFFICIENT`: no treatment from a
  runtime-valid matched pair is temporally eligible; the record supports
  closure adjudication of the neural line without proposing another family.
- operational failures retain their exact reached-boundary evidence and enter
  the precedence above; they do not alter scientific thresholds.

No confirmation target may be consumed from any A10M5R15 terminal.

## Artifacts

- `artifacts/science-contract.json` — exact arms, pairings, hypotheses, gates.
- `artifacts/data-preflight-contract.json` — calendar, normals, and role checks.
- `artifacts/resource-contract.json` — bounded two-L40/two-wave authority.
- `artifacts/predecessor-pin.json` — accepted R14 and PRISM identities.
- `artifacts/verify_scaffold.py` — fail-closed scaffold verifier.
- `execution-readiness-review.md` — independent review and dispositions.
