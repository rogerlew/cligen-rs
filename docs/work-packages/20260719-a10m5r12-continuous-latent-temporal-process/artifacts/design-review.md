# Prospective design review

Disposition: `PASS`

- Month and year are aggregation labels only, not stochastic state clocks.
- The daily transition is the exact discretization of a continuous-time OU
  process and carries state through every calendar boundary.
- The two arms share P2, K2, medium factors, loading network, objectives,
  seeds, streams, and evaluator; the slow process is the sole contrast.
- Daily sine/cosine seasonal and static-site loading is continuous, excludes
  the binary leap-year feature, and uses no observed daily weather input. The
  frozen P2 backbone's inherited leap-year input remains a matched limitation.
- Monthly and annual location and dispersion remain direct training signals;
  paired daily-pattern and conditional-member daily-NLL weights are zero.
- The experiment removes calendar resets but still estimates error through
  fixed calendar bins. Any qualifying candidate requires a later random-origin
  rolling-window sensitivity analysis before promotion.
- Confirmation and solar are sealed.
- Inherited eligibility remains exact, while non-gating actual-series annual
  family diagnostics preserve observed multi-year lag order for interpreting
  the slow-process ablation and report learned time scales.
- A package-local revision-2 calendar/missingness preflight scans the canonical
  corpus and includes the required boundary fixture before authority. It is a
  full authority-time corpus gate. GPU control materialization separately
  reproduces the inherited compact hash-bound expectation.
- Local replay pins the exact inherited comparator binary and requires the six
  per-site PRISM/localization provenance records to equal A10M5R11R2.
- Raw daily streams and fitted adapter checkpoints are collected; selector
  intake replays their hashes, support, exact matrix, and metrics before two
  source/receipt-bound isolated passes.
