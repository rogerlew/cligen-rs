# A7b occurrence-kernel equivalence note

Status: `SCOPE-CORRECTION-ACCEPTED`
Date: 2026-07-14

## Finding

The two registered occurrence candidates are not distinct stochastic model
classes. A second-order binary Markov process and the registered two-phase
semi-Markov process, whose continuation probability changes after the first
day and is geometric from age two onward, have the same four predictive
states.

The state mapping is:

| Second-order history | Semi-Markov state |
|---|---|
| DD | D2+ |
| DW | W1 |
| WD | D1 |
| WW | W2+ |

If `q_s` is the second-order probability of a wet next day and `c_s` is the
semi-Markov continuation probability, then

- `q_DD = 1 - c_D2+`;
- `q_DW = c_W1`;
- `q_WD = 1 - c_D1`; and
- `q_WW = c_W2+`.

The registered recentering is also equivalent. Adding a common logit shift to
all `q` values is exactly the same transformation as subtracting that shift
from the dry-state continuation logits and adding it to the wet-state
continuation logits. The transition matrices are therefore conjugate under
the state permutation above when fitted from the same transitions.

## Numerical check

The A7b implementations differ slightly because the second-order likelihood
and counts begin on series day three, while the semi-Markov implementation can
use series day two. Across the 204 paired station-month cells, that one-record
boundary difference produced:

- maximum mapped transition-probability difference:
  `0.0012456961202288452`;
- maximum mapped stationary-probability difference:
  `0.0000978425282837786`; and
- maximum wet-count-variance difference:
  `0.00679471490979644` days squared.

Both parameterizations nevertheless returned exactly the same 192/204 corpus
feasibility count, the same 31/36 development feasibility count, and the same
12 infeasible station-month cells. The shared amount model and budget root
made their achieved feasible-cell monthly targets agree to a maximum absolute
difference of `6.394884621840902e-14` in dimensionless variance.

## Disposition

This is a P2 design-classification finding, resolved by narrowing the A7b
claim: A7b tested one unique bounded four-state occurrence mechanism through
two registered parameterizations. It did not compare two independent model
classes. The finding cannot reverse the terminal because the unique mechanism
fails the frozen mandatory development surface in both parameterizations and
no A7c candidate is selected.

The stored candidate ranking is not interpreted: its in-sample likelihoods
use unequal day counts by one observation per station, and no candidate
qualified for selection. Any future comparison must establish non-isomorphism
and align likelihood support before freezing its candidate set.
