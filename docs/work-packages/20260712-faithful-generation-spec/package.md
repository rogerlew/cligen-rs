# Faithful Continuous and Observed Generation Specification

Status: `EXECUTED-COMPLETE`
Date: 2026-07-12
Evidence mode: Static

## Objective

Author and register an implementation-grade behavioral specification for
CLIGEN 5.32.3 continuous stochastic and hybrid observed generation. The
specification consolidates the authoritative Fortran behavior, its Rust
translation, and the existing fixture/tap evidence so future generation
profiles can identify their deltas from a stable baseline.

## Scope

Included:

- station-parameter load transformations and the live interpolation paths;
- fixed seeds, burn and warm-up, monthly batch generation, quality-control
  retries, random-stream ownership, and daily draw order;
- continuous (`iopt = 5`) and observed (`iopt = 6`) year/month/day control;
- precipitation, Tmax/Tmin/dew point, radiation, wind, and the duration,
  time-to-peak, and peak-intensity descriptors produced for their daily rows;
- observed substitution/sentinel/EOF behavior and its generator-state
  consequences;
- units, precision, clamps, persistent state, known faithful quirks, and
  behavior-to-source-to-port-to-evidence traceability.

Excluded:

- standalone single-storm (`iopt = 4`) and design-storm (`iopt = 7`)
  orchestration, intake, event-date, and mode-specific output behavior;
- output text formatting, native-f64 behavior, new file formats, and new
  climate-model behavior;
- selection or implementation of an interannual-variation model.

The shared storm calculations are included when they run inside continuous
or observed daily generation. Standalone storm modes are deferred to a later
companion and are considered deprecated in WEPPcloud.

## Authority

- `reference/cligen532/cligen.f`: `tymax` data 602; main setup 702-902;
  block data 1037-1093; `clgen` 1094-1515;
  `dstg` 1651-1788; `dstn1` 1789-1816; `jlt` 1846-1903; `randn`
  1980-2019; `windg` 2020-2122; `timepk` 2188-2236; `sta_parms`
  2656-2970; `day_gen` 2971-3195; observed defaults/intake in `sing_stm`
  3325-3421 and `usr_opt` 3497-3588; `wxr_gen` 3589-3811; `alphb` and
  `r5monb` 3817-4001; `ranset` 4002-4340; QC helpers 4453-4704; ACM
  support 4705-7251; interpolation 7252-7657.
- ADR-0001 and the Rust scientific coding standard define faithful authority,
  precision, and transcendental requirements.
- Existing active interface specs define the `.par`, `.prn`, runspec,
  state-ownership, and generation-profile boundaries.
- Existing golden and interior-tap packages provide executional evidence;
  this package makes static claims over that recorded evidence and does not
  recapture the reference binary unless an ambiguity is found.

## Plan

1. Inventory source units, Rust symbols, state, streams, and existing evidence.
2. Author and register `SPEC-FAITHFUL-GENERATION.md`.
3. Record the mode/branch matrix, parameter-to-output map, and
   source-to-spec traceability artifacts.
4. Record the file-modernization and interannual-variation follow-on as a
   separate design seam, without changing the faithful contract.
5. Perform an independent source/port/spec review and run the repository gates.

## Execution & dispatch

Execute on `main`; start from current `origin/main`, push only to `main`.
Codex authors the package. A separate sub-agent performs the static
source/port/spec consistency review.

## Gates

- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`
- Every generated daily field has a Fortran citation, Rust owner, units, and
  evidence mapping.
- Continuous and observed mode matrices cover every `.prn` sentinel class,
  EOF, monthly refill, and persistent stop state.
- Random-stream consumption and state updates are explicit enough to identify
  the first downstream trajectory divergence caused by a proposed change.
- The faithful spec contains no proposed extension behavior.

## Exit criteria

`EXECUTED-COMPLETE` requires the registered spec, all traceability artifacts,
an independent review with findings dispositioned, and green repository gates.
A source ambiguity that cannot be resolved statically is an
`EXECUTED-HOLD-REFERENCE-CAPTURE` outcome naming the exact capture required.

Achieved 2026-07-12: the spec is registered and active; every artifact above
is present; the independent static review dispositioned all High/Medium
findings; no new reference capture was required; and all repository and
package-specific gates passed as recorded in `artifacts/gate-results.md`.

## Artifacts

- `artifacts/source-to-spec-traceability.md`
- `artifacts/mode-branch-matrix.md`
- `artifacts/parameter-to-output-map.md`
- `artifacts/interannual-variation-follow-on.md`
- `artifacts/review.md`
- `artifacts/gate-results.md`
