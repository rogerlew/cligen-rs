# A10M5R1 gate results

- Prospective scripts, hypotheses, controls, and stop rules published: PASS.
- Four one-L40 allocations at no more than 30 minutes each: PASS (120
  requested GPU-minutes; 885 actual GPU-seconds).
- One pinned CPU and explicit one-thread framework/BLAS controls: PASS.
- Protected development/confirmation roles unread: PASS.
- Exact predecessor candidate identity: PASS (12/12 hashes).
- Export size at or below 250 MiB: PASS (152,204 bytes).
- Cold load at or below 15 seconds: PASS (1.206 seconds).
- Warm absolute and 5x/10x runtime contract: PASS (maximum ratio 3.8199).
- Benchmark dispersion: PASS.
- Actual fresh-process RSS at or below 2 GiB: PASS (628--635 MB external
  maximum; 521--525 MB `/proc` steady RSS).
- R4 raw/sanitized evidence, job-local absence, exact durable cleanup, and
  toolkit close: PASS.
- Repository toolkit tests, formatting, clippy, and Rust tests: PASS.

R1 and both R2 roles exposed package-authored lifecycle/source defects. Their
measurements are retained but do not substitute for R4's valid lifecycle.
They are explicitly dispositioned and charged in the resource ledger.

Terminal: `A10M5R1-EXPORT-REMEDY-READY`.
