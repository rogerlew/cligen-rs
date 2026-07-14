# Invalidated A5d1 v2 Execution

Status: `INVALIDATED-IMPLEMENTATION-DEFECT`

The v2 run closed its complete 306-cell matrix, but it cannot support the A5d1
decision. In rare months with fewer than one wet day per library block on
average, the implementation divided uniform precipitation-bin and storm-
descriptor sums by `max(mean_wet_days, 1)` rather than the actual positive
wet-day denominator. Consequently, uniform weights could violate constraints
whose stated reference was the same uniform library.

Phase-I replay exposed the contradiction after the provisional v2 hold. The
formula-only correction is recorded in `pre-solver-freeze-amendment-002.json`.
No target, tolerance, algorithm, seed, pool, objective, or selection rule was
changed. The v2 artifacts remain under `invalidated-v2-*` names and are
excluded from terminal evidence.

## Retained identities

- v2 freeze: `351b46ff2e0d2d92c9424ff6412822ae56911cca94b3a0b8e71dc8159b39500a`
- v2 library manifest: `949baeab65b2dddf4e65ae845ef173c2afcea1b3d4519c124ccf65556f7f4c94`
- v2 feature manifest: `7eaca28ac6936a8dba7f4c4696ed0a4b8a0cf599f7c0ac4d08112a0956d9ca70`
- v2 marginal results: `47e8e241b15dd6fceccaaa69ddfcc424913cf0ee6e3034488a543114feef746d`
- v2 path results: `27e7c8ead5c394e596e895dafe73db743f68b9331d7dd5a865aac50c62f601e6`
- v2 aggregate results: `5edb09da10ab9a9e9b021e16d0535564ca437f4bdf5e5ec59788c950539798ce`
- v2 provisional decision: `8f4d76ef2a80631fa518a9b9ba3db834771fa6be35fef14a3dcece8010b54163`
- v2 report: `14bb6d1491c64fe0f91270ae02907c4efcb96b8c893fbce64b8a450b457e2fdb`
- v2 phase-I diagnostic: `ce8fc57170a1b59f433160c8c04d8a6e2082086f00c374c1bb98fe1ad294ffe9`
