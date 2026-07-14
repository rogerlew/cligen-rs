# A5d1 Selector Feasibility Report

Decision: `HOLD`
Terminal status: `EXECUTED-HOLD-PATH-INFEASIBILITY`

## Question and boundary

This development-only experiment asked whether one prospectively frozen, bounded complete-year selector contract can satisfy the marginal and finite-path requirements at all 17 exposed stations. It did not inspect confirmation data, mutate daily physical values, change faithful generation, or authorize a public candidate.

## Methods

A single burn-0 256-year `faithful_5_32_3 + qc_filter: off` library was regenerated twice per station. Nested 128- and 256-year prefixes supplied complete blocks. Binary64 HiGHS linear programs selected nonnegative weights under fitted monthly and uniform-library preservation constraints while minimizing normalized distance to six detrended-Daymet annual raw moments. Three bounded path algorithms and three fixed seeds constructed 100-year paths; every 30-year result was its exact prefix. Dependence, calendar, reuse/cooldown, cross-boundary, physical-row identity, and resource invariants were replayed independently.

## Marginal results

| Pool | Passing stations | All 17 |
|---:|---:|:---:|
| 128 | 13/17 | no |
| 256 | 17/17 | yes |

## Finite-path results

| Pool | Algorithm | Passing station-seed cells | All 51 |
|---:|---|---:|:---:|
| 128 | `guarded_replacement` | 0/51 | no |
| 128 | `weighted_permutation` | 0/51 | no |
| 128 | `state_persistent_different_block` | 0/51 | no |
| 256 | `guarded_replacement` | 0/51 | no |
| 256 | `weighted_permutation` | 0/51 | no |
| 256 | `state_persistent_different_block` | 0/51 | no |

## Conclusion

No global contract passed. A5d1b must diagnose the first common finite-path failure under the frozen marginal weights before introducing another path algorithm. The frozen rules were not relaxed after outcomes were opened.

## Evidence identities

- Pre-solver freeze: `9b408216af554a1f2b773e2ffd1560c731a245de1cf1e155b89b1dcbaaf03aa7`
- Result record: `eb16a718694ee593f79757137490c3ea86efcfe14eba6a4420c8352bc65176ed`
- Full path matrix: `2c84be4d69b969677ba9482588e845b4a90289b58a0d873beb23aaea6bdad98f` (reproducible target evidence; not committed)
