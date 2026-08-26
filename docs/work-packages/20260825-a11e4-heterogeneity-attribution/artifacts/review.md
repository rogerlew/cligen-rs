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

## Completed evidence review

The independent reviewer authenticated all 12 manifest-bound A11E2/A11E3
current and source-commit blobs, every A11E4 source blob at `dfef66c`, the
evidence self-hash, and the receipt output hashes and sizes. The reconstruction
found 160 unique station/member rows, 20 stations, the frozen regime sizes, and
a rank-eight joint design. Independent OLS reproduced full
`R²=0.1526293460380176`, ranked-distance coefficient
`0.0372548103848221`, and mismatch coefficient `-0.01677074939564871`.

All eight member-omission and 20 reranked/rescaled station-omission fits matched
the recorded ranges and sign gates. Exhaustive enumeration reproduced all
1,327,104 assignments, zero degenerate assignments, extreme counts 1,232,992
and 1,324,688, and adjusted p-values `0.9290846836419753` and
`0.9981794945987654`. Replay evidence and decision hashes matched the first
execution. Confirmation and production flags remained false.

Final closure disposition: **GO — NO_STABLE_METADATA_ASSOCIATION**, with no
remaining P0/P1. Neither frozen predictor supports a simple selector refinement,
and the package correctly stops without confirmation access or an automatic
successor.
