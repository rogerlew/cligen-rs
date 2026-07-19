# A10M5R4R2R1R1 — Evaluation Year-Axis Remedy

Status: `EXECUTED-HOLD-LEAP-CENTURY`
Date: 2026-07-18
Evidence mode: Prospective zero-allocation scoring correction
Starting branch and push target: `main`, push `main`

## Objective

Complete the unchanged R2R1 temporal adjudication from its exact collected
neural and comparator evidence after correcting only the out-of-range
synthetic calendar labels used by observation year-block bootstrap resampling.

## Boundary

This package may read the authenticated R2R1 toolkit evidence, the exact
retained comparator tree, A10M1's six frozen observation records, and the
already-published temporal/evaluation contracts. It authorizes no Slurm job,
GPU allocation, model reconstruction, comparator regeneration, role access,
metric change, component-scale change, threshold change, or selector change.

The correction maps bootstrap block position `i` to year `2400 + 8*i` for a
source block containing February 29 and to `2401 + 8*i` otherwise. The years
are unique, strictly increasing, within 2400--2633, preserve source leap-day
validity, and remain noncontiguous so the frozen exclusion of inter-block
transitions and spells is unchanged.

## Inputs

- R2R1 toolkit collection receipt SHA-256:
  `57ebbb055620697d8db424ccf32214c430a62bd2f33a8362fd41b542d0af0616`;
- R2R1 toolkit terminal receipt SHA-256:
  `e9827a06d4691430c2cd32eeb728e2aa4be109675cc84b54d21211a3a8005c3b`;
- comparator tree: 354 files, 280,551,300 bytes, canonical tree SHA-256
  `c4d7bf9c2b8441b89ceda42ec1ef5e7976ee533f998eff473bece2f967154607`;
- parent evaluation contract and six-site roster unchanged.

## Plan

1. Verify every bound input identity and prove the parent published no score.
2. Reparse the retained comparator daily files and authenticated neural stream
   metrics without regenerating either arm.
3. Run the unchanged 1,000-replicate paired bootstrap with the corrected
   in-range, leap-preserving synthetic labels.
4. Publish the typed temporal decision, reconcile the campaign, clean the
   retained comparator scratch, and run repository gates.

## Gates

- `artifacts/verify_freeze.py` emits `A10M5R4R2R1R1-FREEZE-READY`;
- exact comparator tree and toolkit receipts match the bound identities;
- no parent score exists before successor execution;
- scoring output is deterministic on two complete runs;
- protected roles remain sealed and GPU use remains zero; and
- repository formatting, clippy, and test gates pass.

## Exit criteria

Issue `A10M5R4R2R1R1-TEMPORAL-READY` with the retained capacity set and A10M5R5
authority if at least one capacity passes, otherwise the unchanged typed
no-eligible-capacity hold.

## Artifacts

- `artifacts/jobs/score.py` — identity-bound zero-regeneration scorer;
- `artifacts/verify_freeze.py` — input and correction verifier.

## Disposition

The exact input identities passed, and no model or comparator was rerun. The
first bootstrap replicate stopped before score publication because block
position 25 assigned a leap source block to year 2600, which is divisible by
100 but not 400 and therefore not Gregorian leap. Terminal:
`HOLD-A10-EVALUATION-LEAP-CENTURY`. The zero-allocation R2 successor uses
`2000 + 16*i`, whose complete 2000--2464 range contains no non-400-divisible
century, and `+1` for nonleap blocks.
