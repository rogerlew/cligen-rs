# Execution disposition

## Bound inputs

- R2R1 collection receipt SHA-256:
  `57ebbb055620697d8db424ccf32214c430a62bd2f33a8362fd41b542d0af0616`;
- R2R1 terminal receipt SHA-256:
  `e9827a06d4691430c2cd32eeb728e2aa4be109675cc84b54d21211a3a8005c3b`;
- retained comparator tree: 354 files, 280,551,300 bytes, canonical tree
  SHA-256 `c4d7bf9c2b8441b89ceda42ec1ef5e7976ee533f998eff473bece2f967154607`;
- six observation records and the evaluation contract inherited unchanged
  from R2R1.

## Execution

The package verifier proved all century-safe leap/nonleap labels and exact
input identities before scoring. The scorer reparsed the existing 288 neural
streams and 96 comparator streams without reconstruction or regeneration. It
ran the frozen 1,000-replicate paired bootstrap twice with seed 410542. The
two complete outputs were byte-identical at SHA-256
`d1f877f0dc298f129019dbf7d093de8033f9df10d5a694f3038c9e76b832e0a6`.
Protected roles remained unopened.

This successor used zero Slurm jobs and zero GPU-minutes. Its parent R2R1 used
six successful single-attempt jobs, 1,238 actual GPU-seconds and 24
ceiling-rounded GPU-minutes; combined with R2's three charged minutes, the
campaign used 27 of its 185-minute ceiling. Retry and recovery reserves were
unused.

## Decision

P1 failed both temporal noninferiority limits with a 2.594775856552054 upper
90% bootstrap median regime ratio and a 3.782817495745157 maximum regime
ratio. P2 also failed, at 2.564622468950476 and 3.9502821535166905. P2's
probability of at least 10% reduction was 0.0. The retained capacity set is
empty, terminal `HOLD-A10-NO-TEMPORALLY-ELIGIBLE-CAPACITY` is final for this
frozen P1/P2 hypothesis, and A10M5R5 is not authorized.

## Cleanup

The toolkit verified job-local absence, removed the exact remote durable root,
and closed normally before local scoring. After both deterministic scores and
the bound comparator-tree audit, the exact retained local comparator scratch
root was moved to
`/Users/roger/.Trash/a10m5r4r2r1-scratch-20260718`. It is absent from the
evaluation root but remains recoverable until the operator empties Trash. The
two external score copies remain as a reproducibility cross-check; the
canonical typed decision is committed with this package.
