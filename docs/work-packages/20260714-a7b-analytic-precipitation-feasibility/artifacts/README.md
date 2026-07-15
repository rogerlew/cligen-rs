# A7b artifacts

This directory contains the frozen analytic-feasibility contract,
deterministic fits, moment-budget certificates, terminal decision, and review
evidence for A7b.

- `design.md` and `feasibility-contract-v1.json` define the prospective model,
  numeric, fit, RNG, and decision boundaries.
- `analyze-a7b.py`, `verify-a7b.py`, and `freeze-a7b.py` are the deterministic
  analysis, independent verification, and freeze programs.
- `pre-analysis-freeze-v1.json` binds methods and parent inputs;
  `pre-analysis-amendment-001.json` records the bounded A7a-key correction made
  before candidate-data access.
- `a7b-analysis-v1.json`, `a7b-decision-v1.json`, and `findings.md` are the
  reproducible canonical output.
- `post-analysis-equivalence-review.md` records the discovered equivalence of
  the two occurrence parameterizations; `verify-equivalence.py` reproduces the
  paired-cell evidence.
- `review.md` and `gate-results.md` close the accuracy, scope, consistency, and
  repository gates.
