# A9c gate results

Date: 2026-07-15
Terminal: `HOLD-A9C-GATE-CALIBRATION`

## Scientific and evidence gates

- PASS — exact A9a/A9b predecessor inputs verified and all 20 A9b fixture
  groups replayed.
- PASS — the role freeze predates station-series access.
- PASS — 40 Daymet and 24 USCRN normalized objects rehash and validate;
  180 USCRN station-year source accesses are recorded.
- PASS — the access firewall reports zero A9a confirmation-series access.
- PASS — candidate-blind null calibration contains seven objective families,
  two horizons, and 500 identities per family/horizon: 7,000 total and 14
  frozen thresholds.
- PASS — all five fits completed before the stop validate against the official
  fit schema and self-hash.
- HOLD UNDER FROZEN A9C RULES — hot-arid development event support is 136 events at AZ Yuma 27 ENE
  and 97 at CA Stovepipe Wells 1 SW. Both stations miss the 150-event floors
  for time-to-peak and peak ratio and the 200-event floor for joint
  dependence. Three mandatory cells therefore have 0/2 available stations.
- DISPOSITIONED — those per-station floors were not derived from an A9 power
  or precision calibration. Report revision 2 treats the outcome as a design-
  rule mismatch and directs candidate-blind grouped support calibration in
  A9c2; no A9c result is recalculated.
- NOT RUN BY DESIGN — candidate development scoring, the 31-objective
  candidate vector, Pareto ranking, selector replay, A9d freeze, and
  confirmation evaluation are downstream of the first failed gate.
- PASS — the public report and consolidated review have zero open P1/P2
  findings.

## Reproduction and repository gates

Commands executed from repository root:

```text
python3 -m unittest discover -s research/a9c/tests -v
python3 docs/reports/verify-report.py --self-test
python3 docs/reports/verify-report.py \
  docs/reports/a9c-observed-development-availability-report.manifest.json
python3 docs/work-packages/20260715-a9c-observed-development/artifacts/verify-a9c.py
git diff --check
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
```

All commands passed. The package verifier reports:

```text
PASS: predecessor; 64 observed objects; 180 source accesses; 7000 null
replicates; 5 fits; 3-cell mandatory availability hold; zero
confirmation/runtime access
```

A scoped authored-file trailing-whitespace scan passed. The copied NOAA
source-format documents retain their source bytes, including source trailing
spaces. Every retained file under `artifacts/large/` resolves to the Git LFS
filter. `git diff -- crates reference/cligen532` is empty.

Coverage/CRAP is not triggered because A9c changes no production function
under `crates/`.
