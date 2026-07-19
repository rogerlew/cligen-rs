# Execution disposition

Terminal: `HOLD-A10M5R9-RESIDUAL-ARCHITECTURE-NOT-SUPPORTED`

Run `a10m5r9-climate-normal-residual-r0`, Slurm job `1014027`, completed on
`node03` with exit 0 after 811 GPU-seconds (14 charged GPU-minutes). The
accepted P1 seed-147031 checkpoint reconstructed exactly. The complete 1,200
candidate-fit and 240 fit-validation corpus passed the revision-2 Daymet
calendar preflight before resource reservation and again inside the
allocation. Fit-validation remained gradient-free and no protected role was
opened.

The monthly residual supplied real stochastic signal but did not advance the
architecture. Relative to the identical frozen climate-normal baseline, it
reduced the mean monthly/annual interannual-dispersion error by 15.15%, meeting
that gate, and improved the family-balanced climate score by 4.41%, missing
the frozen 5% gate. Every individual climate block and the daily proper-NLL
guard passed relative to the baseline. The residual arm nevertheless scored
2.7422 climate / 4.6398 NLL against accepted P1 at 2.5904 / 4.1787, so both P1
guards failed. The deterministic selector retained no arm.

The frozen baseline was byte-identical before and after residual training. Its
12,231 parameters trained for 24 epochs; the 30-parameter residual trained for
32 epochs and learned persistence from 0.2048 through 0.9789 across its six
dimensions. Both selected checkpoints occurred at their prospective epoch
ceilings. This is a learning-curve caution, not permission to reinterpret or
retry the failed decision.

All nine publication gates passed. Toolkit observation, collection, job-local
and durable cleanup, and terminal close passed; recovery was not invoked. The
sanitized evidence archive is 71,680 bytes with SHA-256
`3933839274ea2f8dcda1dacc73f0e61fbd9b1e25e3e70f1a0b36b268198ffaff`,
and the exact remote root is verified absent.

## Recommended next architecture

Do not add solar or broaden the input relationship set yet. The ablation
separates the result cleanly: the monthly residual improved the target
stochastic behavior, while replacing P1 with the smaller explicit-normal
baseline created the unrecovered climate/proper-fit deficit.

The least-complex next prospective test is therefore a **frozen-P1,
mean-preserving monthly residual adapter**. It should compare exact frozen P1
against that same P1 plus the centered six-dimensional monthly residual,
train only the adapter on the registered stochastic objective, and retain the
same all-240 decision surface. This tests whether the useful residual mechanism
can be attached without discarding P1's stronger baseline. Solar
radiation/latitude/day-of-year/precipitation coupling remains the first
generalization only after a core adapter passes.
