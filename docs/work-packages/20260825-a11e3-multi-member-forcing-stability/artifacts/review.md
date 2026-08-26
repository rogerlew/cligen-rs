# A11E3 independent review

## Prospective review

Initial disposition: **HOLD**, with no P0 and four P1 publication blockers:

- authenticate the inherited strategy lab before any dependency import;
- freeze and receipt Python/NumPy because new Philox members depend on it;
- make the JSON schema pin every scientific manifest value; and
- require the exact authenticated 20-station by eight-member Cartesian grid,
  rather than accepting an uneven grid with the same total count.

The corrected source authenticates A11E1, A11E2, and strategy bytes against
their exact commits before import; requires Python 3.12.13 and NumPy 2.3.5;
const-pins the complete manifest in its schema; and uses the exact station
roster for completeness and member-0 replay. New tests cover dependency and
runtime drift, schema identity, uneven grids, nonfinite metrics, duplicates,
missing cells, invariants, and ties.

Final prospective disposition: **GO for source publication**, with no remaining
P0/P1. The independent reviewer reran 17/17 synthetic tests, reproduced manifest
digest `9e8bf3b3eac8cff8c81c4e96c67532a891ccfbc71fcbb3313dd2a63fe665b8b7`,
and passed `git diff --check`. Member-0 RNG identities, 30,720 collision-free
daily ordinals, only-location arm difference, calendar/role ordering, all-16
rule, and confirmation firewall were accepted. No observed A11E3 or sealed
confirmation values were accessed.

## Completed-evidence review

Scientific evidence disposition: **GO**. The independent reviewer reproduced
published source `ac254ee4fc2bc0073a4f4c351e555cc517c49f3d`, runtime and all
A11E1/A11E2/strategy/input/output identities, evidence self-hash `c8e302b3`,
calendar masks/counts, RNG identity counts, fit and selector/location hashes,
the exact 20x8 paired grid, finite metrics, zero invariants, member-0 metrics
and stream hashes, all per-member medians/deltas, and confirmation=false.

All 16 deltas are strictly negative; `STABLE_FOR_EXPLORATION` is correct. The
scientific output hashes replayed exactly: calendar `49d86f2d`, fit `5cdcddec`,
evidence `834d9af5`, and decision `06537916`. The result is not stationwise
dominance: precipitation improves in 90/160 cells, temperature in 119/160,
both in 66/160, only four stations improve both in all members, and six never
do. The sole closure P1 was terminal-record reconciliation; those surfaces and
the two-pass replay record are now reconciled. No automatic successor or
confirmation is recommended. Final closure disposition: **GO**, with no
remaining P0/P1.
