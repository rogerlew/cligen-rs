# Execution disposition

Terminal: `HOLD-A10-ARCHITECTURE-HYPOTHESIS-MIXED`

Run `a10m5r7r2-architecture-r0`, Slurm job `1014017`, completed successfully
on `node03` with exit 0 after 261 GPU-seconds (five charged GPU-minutes). The
accepted P1 seed-147031 checkpoint reconstructed exactly. All three 30-year,
eight-member, six-site inference modes were finite and physically supported;
3,384 registered component residuals were published. Candidate-fit was the
only normalization/training role and no protected role was opened.

Generated feedback did not advance. Its family-balanced error was 3.1449
versus 2.6821 open-loop, a 17.26% degradation. It violated the monthly-
climatology and precipitation-distribution nondegradation guards. Observation
conditioning improved the aggregate by only 9.84%, below the frozen 25%
threshold. The accepted residual shares were temperature 31.61%, precipitation
distribution 19.38%, annual dependence 17.61%, monthly climatology 17.47%, and
occurrence/spells 13.93%; none met a registered single-mechanism dominance
threshold. The deterministic selector therefore issued `mixed_hold`.

No full candidate streams were produced and the unchanged temporal score was
correctly recorded as not reached. This preserves the prior empty temporal
retained set.

Toolkit observation, collection, job-local cleanup, durable cleanup, and close
all passed. Recovery was not invoked. The collected evidence archive was
2,990,080 bytes with SHA-256
`aac887ebd29ef3b8899c39bdc8174967f9b1d0d24fc1b4af4eb2756e19ba4d8a`;
the exact remote run root was independently verified absent.

## Recommended next architecture

The evidence does not support making raw autoregressive feedback the next
architecture. The dominant pattern is a transferable seasonal-baseline error:
winter temperatures are too warm, summer temperatures are too cold, and low
precipitation quantiles are badly biased, while one-step observation state
provides only modest benefit.

The least-complex next prospective family should therefore be a
**climate-normal-conditioned residual state-space model**:

1. supply external monthly precipitation/Tmax/Tmin normals as transferable
   site conditioning;
2. predict coupled daily residuals around explicit seasonal temperature and
   precipitation baselines rather than absolute weather directly;
3. retain a small latent residual state for spells and annual dependence; and
4. compare a baseline-only residual model against the same model with latent
   dynamics before considering scheduled-sampling or generated feedback.

This is a combined architecture hypothesis, not one of the single-mechanism
branches that failed the frozen selector. Fitting it requires a new scientific
contract and resource authorization; R2 does not open that work automatically.
