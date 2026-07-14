# A5d1 Selector Feasibility Report

Decision: `HOLD`
Terminal status: `EXECUTED-HOLD-STRUCTURAL-INFEASIBILITY`

## Question and boundary

This development-only experiment asked whether one prospectively frozen, bounded complete-year selector contract can satisfy the marginal and finite-path requirements at all 17 exposed stations. It did not inspect confirmation data, mutate daily physical values, change faithful generation, or authorize a public candidate.

## Methods

A single burn-0 256-year `faithful_5_32_3 + qc_filter: off` library was regenerated twice per station. Nested 128- and 256-year prefixes supplied complete blocks. Binary64 HiGHS linear programs selected nonnegative weights under fitted monthly and uniform-library preservation constraints while minimizing normalized distance to six detrended-Daymet annual raw moments. Three bounded path algorithms and three fixed seeds constructed 100-year paths; every 30-year result was its exact prefix. Dependence, calendar, reuse/cooldown, cross-boundary, physical-row identity, and resource invariants were replayed independently.

## Marginal results

| Pool | Passing stations | All 17 |
|---:|---:|:---:|
| 128 | 10/17 | no |
| 256 | 14/17 | no |

## Finite-path results

| Pool | Algorithm | Passing station-seed cells | All 51 |
|---:|---|---:|:---:|
| 128 | `guarded_replacement` | 10/51 | no |
| 128 | `weighted_permutation` | 10/51 | no |
| 128 | `state_persistent_different_block` | 6/51 | no |
| 256 | `guarded_replacement` | 5/51 | no |
| 256 | `weighted_permutation` | 10/51 | no |
| 256 | `state_persistent_different_block` | 5/51 | no |

## Conclusion

No global contract passed. A5d1a must diagnose which frozen station-surface or annual-marginal constraints exclude a common pool before any selector-family expansion or tolerance change. The frozen rules were not relaxed after outcomes were opened.

## Evidence identities

- Pre-solver freeze: `351b46ff2e0d2d92c9424ff6412822ae56911cca94b3a0b8e71dc8159b39500a`
- Result record: `5edb09da10ab9a9e9b021e16d0535564ca437f4bdf5e5ec59788c950539798ce`
- Full path matrix: `27e7c8ead5c394e596e895dafe73db743f68b9331d7dd5a865aac50c62f601e6` (reproducible target evidence; not committed)
