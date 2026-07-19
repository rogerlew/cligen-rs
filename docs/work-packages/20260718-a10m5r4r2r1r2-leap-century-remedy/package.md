# A10M5R4R2R1R2 — Leap-Century Evaluation Remedy

Status: `FROZEN-LOCAL-EXECUTION`
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
