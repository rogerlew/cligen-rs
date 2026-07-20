# A10M5R11 — Retained Adapter Temporal Generalization

Status: `SCAFFOLDED`
Date: 2026-07-19
Evidence mode: Mixed
Starting branch and push target: current `main`, push `main`

## Objective

Run the three A10M5R10 retained residual adapters through the ratified A10
realized-temporal protocol and carry every temporally eligible configuration
forward. The claim is reproduction of stochastic monthly and yearly climate,
not observed day-to-day weather.

## Frozen matrix

The only candidate roles are:

| Role | Architecture | Capacity | Frozen control |
| --- | --- | --- | --- |
| `annual-monthly-residual-adapter-k1` | annual/monthly persistent residual | K1 | P1 |
| `monthly-residual-adapter-k2` | monthly persistent residual | K2 | P2 |
| `annual-monthly-residual-adapter-k2` | annual/monthly persistent residual | K2 | P2 |

Each role trains seeds 147031, 271828, and 314159 under the exact R1R4
objective, then generates 100 Gregorian years from 2001 for eight members at
one frozen fit-validation site in each of six regimes.

## Temporal authority

Metrics, component scales, faithful and localized stochastic-PRISM
comparators, 1,000 paired bootstrap replicates, seed 410542, and the 1.25/1.50
noninferiority gates are inherited from A10M5R4R2. The A10M5R4R2R1R2
leap-century correction is normative. Missing Daymet values are never filled.
All eligible configurations continue; no new winner or parsimony rule is
introduced.

## Solar boundary

Solar is closed here. The downstream design direction is a deterministic
latitude/day-of-year astronomical envelope plus a stochastic clearness/cloud
residual coupled to generated precipitation and temperature. That later model
must remain generative and cannot condition on observed daily weather.

## Resources and execution

One 30-minute one-L40 control predecessor and three 90-minute one-L40
candidate roles are allowed, with no more than two live primary jobs. A
five-minute exact-node cleanup reserve yields a 305 GPU-minute ceiling. Each
role has one attempt. Confirmation remains sealed.

## Exit criteria

`A10M5R11-TEMPORAL-READY` requires at least one complete, support-valid
configuration to pass both inherited temporal gates. Otherwise the scientific
terminal is `HOLD-A10M5R11-NO-TEMPORALLY-ELIGIBLE-CANDIDATE`. Identity,
calendar, evidence, resource, or cleanup failures receive exact operational
holds and no scientific interpretation.

## Artifacts

- `artifacts/temporal-contract.json` — inherited protocol and three-role matrix;
- `artifacts/sites.json` — exact six-regime roster;
- `artifacts/solar-design-note.md` — downstream procedural/stochastic boundary;
- `artifacts/jobs/` — immutable control, training, stream, and selection code;
- execution, temporal, replay, cleanup, review, and gate records added at close.
