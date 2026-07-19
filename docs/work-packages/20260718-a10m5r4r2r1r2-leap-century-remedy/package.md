# A10M5R4R2R1R2 — Leap-Century Evaluation Remedy

Status: `EXECUTED-HOLD-NO-TEMPORALLY-ELIGIBLE-CAPACITY`
Date: 2026-07-18
Evidence mode: Prospective zero-allocation scoring correction
Starting branch and push target: `main`, push `main`

## Objective and boundary

Complete the unchanged temporal score from the exact R2R1 neural/comparator
matrix after R1 exposed year 2600 as a nonleap Gregorian century. No generator,
comparator, role, metric, scale, threshold, selector, or resource boundary may
change. No Slurm or GPU work is authorized.

## Corrected mapping

Bootstrap block position `i` maps to `2000 + 16*i` when the source block
contains February 29, and to that year plus one otherwise. For all 30
positions, base years are divisible by 16. The only century years in the
2000--2464 interval are 2000 and 2400, both divisible by 400. Thus every base
is Gregorian leap, every `+1` year is nonleap, labels are unique and strictly
increasing, and all adjacent block labels remain noncontiguous.

## Inputs and gates

The input receipt and comparator identities are exactly those frozen by R1.
`artifacts/verify_freeze.py` proves all 30 leap/nonleap mappings, input hashes,
and absence of any prior score, then emits `A10M5R4R2R1R2-FREEZE-READY`.
Two full scores must be byte-identical before disposition.

## Exit criteria

Issue the unchanged typed temporal decision and A10M5R5 authority only if at
least one capacity passes. Otherwise retain the exact no-eligible-capacity
hold. Clean retained comparator scratch and pass repository gates.

## Disposition

The century-safe mapping passed for all 30 observation blocks. The scorer read
the exact authenticated R2R1 neural collection and retained comparator tree;
it regenerated neither models nor comparators and used no Slurm or GPU
allocation. Two complete scoring runs produced byte-identical output with
SHA-256 `d1f877f0dc298f129019dbf7d093de8033f9df10d5a694f3038c9e76b832e0a6`.

Neither capacity passed the unchanged temporal noninferiority gates. P1's
90% upper bootstrap bound on the median regime ratio was 2.594775856552054 and
its maximum point regime ratio was 3.782817495745157. P2's corresponding
values were 2.564622468950476 and 3.9502821535166905, against limits 1.25 and
1.5. P2's bootstrap probability of at least a 10% reduction relative to P1
was 0.0, against 0.9. Therefore the retained set is empty, terminal
`HOLD-A10-NO-TEMPORALLY-ELIGIBLE-CAPACITY` is issued, and A10M5R5 is not
authorized. Any new architecture or model-family search requires a new
scientific decision; this package does not select one after observing the
result.

## Result artifacts

- `artifacts/temporal-decision.json` — complete typed score and comparator
  provenance;
- `artifacts/determinism.json` — two-run byte-identity record;
- `artifacts/execution-disposition.md` — execution, resource, cleanup, and
  decision summary;
- `artifacts/resource-ledger.md` — package and aggregate GPU accounting;
- `artifacts/verify_result.py` — fail-closed result verifier; and
- `artifacts/gate-results.md` — repository and package gate transcript.
