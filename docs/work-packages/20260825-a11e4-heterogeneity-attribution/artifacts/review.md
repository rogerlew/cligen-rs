# A11E4 independent review

## Prospective review

Initial review held publication on three successive arithmetic/coverage issues:

- max-|t| equality used different scalar and batched floating-point shapes;
- joint LOMO/LOSO and incremental-R² wiring lacked integration coverage; and
- degenerate permutation fits had an implicit studentization rule inconsistent
  with observed OLS failure semantics.

The corrected source freezes a `1e-12` relative equality tolerance, verifies
that identity is actually counted, and checks vectorized exact counts against a
scalar oracle. A synthetic integration oracle independently reconstructs all
eight LOMO and twenty reranked/rescaled LOSO fits, predictor wiring, sign gates,
and both incremental-R² deltas. Observed/stability fits fail closed at the
common scale-aware residual tolerance; degenerate permutation assignments use
the explicitly frozen conservative signed-infinity/zero rule and are counted.

Final prospective disposition: **GO for source publication**, with no remaining
P0/P1. The independent reviewer reran 15/15 synthetic tests, reproduced manifest
digest `358ff235f70aa69b7216419e8864e06c312a84457dbc08df5e8997381442f666`,
and passed `git diff --check`. No A11E4 association, raw observed series, or
confirmation evidence was accessed.
