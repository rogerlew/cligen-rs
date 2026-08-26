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
