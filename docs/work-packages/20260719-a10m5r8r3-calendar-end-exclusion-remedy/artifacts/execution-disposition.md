# Execution disposition

Terminal: `HOLD-A10M5R8-CORE-OBJECTIVE-NOT-SUPPORTED`

The unchanged experiment completed in R3. Slurm job `1014025` ran on one L40
on node03, exited 0 after 664 seconds, and passed every operational gate. The
accepted P1 seed-147031 control reconstructed exactly. All 1,200 candidate-fit
and 240 fit-validation points had eligible exact eight-year masked-calendar
windows. Fit-validation remained gradient-free; protected roles remained
sealed.

The climate-statistics treatment improved the full fit-validation family-
balanced score from 2.582726 to 2.212066, or 14.3515%. This is real but below
the prospectively frozen 15% improvement gate. More importantly, it failed
three block guards and the daily proper-score guard:

- annual interannual dispersion improved 18.57%;
- within-month daily dispersion improved 64.88%;
- precipitation-temperature dependence improved 3.12%;
- wet occurrence/amount degraded 8.41%, within the 10% guard;
- annual location degraded 44.74%;
- monthly interannual dispersion degraded 11.70%;
- monthly location degraded 10.13%; and
- core daily proper NLL degraded 110.59%, from 4.178742 to 8.799844.

The treatment remained finite and physically supported, and its best
checkpoint occurred at the frozen maximum epoch 40. No outcome-time epoch,
weight, threshold, or seed extension is allowed. No candidate was selected.

## Scientific interpretation

The objective repair successfully transfers pressure toward stochastic
dispersion—especially within-month variability—but the unchanged absolute-
weather P1 architecture trades that gain against seasonal/annual location and
proper distribution fit. The result therefore does not support adding solar
radiation to this architecture yet.

The next prospective model should be the previously indicated climate-normal-
conditioned residual state-space family: explicit monthly precipitation/Tmax/
Tmin baselines own location, while a residual stochastic component owns
dispersion and dependence. Its first comparison should be baseline-only versus
the same baseline plus a small latent residual state. Solar radiation remains
the first coupled extension only after that core architecture passes.

Toolkit collection, recovery release, job-local cleanup, durable cleanup, and
close all passed. The complete sanitized comparison/training evidence is
retained beneath the private R3 toolkit publication tree and bound by hashes in
`artifacts/toolkit-records.md`.
