# Scaffold gates

- Four arms only: E0, E1, E2C, E2.
- Matched attribution pairs only: E0/E1 and E2C/E2.
- E0 is the matched control, not the strongest prior incumbent; R14 arm D stays
  visible at 2.162/3.517.
- E0/E1 use P2 with the corrected 340,000 total ceiling.
- E2C/E2 are explicit backbone-free replacements below 330,000 total.
- Exact totals are E0 278,747, E1 279,467, E2C 2,040, and E2 2,760; matched
  deltas are limited to the frozen normals location-mapping columns.
- One shared strictly positive attribution margin is calibrated from
  candidate-blind null/control evidence and frozen before output; it is applied
  to the bootstrap median regime-ratio upper-90% within each matched pair.
- Temporal gates remain 1.25/1.50 at both nested horizons.
- Runtime is ADR-0006: pass below 5×, warning from 5× to below 30×, failure at
  30× or greater.
- READY is per treatment: that treatment and its matched control pass
  engineering/runtime, and the same treatment passes temporal and attribution;
  evidence may not be mixed across E1/E2.
- Exact PRISM bundle and embedded manifest hashes are pinned.
- Calendar/missingness/normals preflight precedes scarce-resource reservation.
- One 30-minute control, one two-L40 240-minute portfolio, two waves, two
  isolated children per wave, five recovery minutes, 515 total.
- No confirmation, solar, spatial, promotion, or production authority.
- Package verifier, JSON parsing, Python compilation, repository gates, and
  `git diff --check` must pass before publication.

The scaffold is complete when these contracts are internally consistent and
the independent readiness review has no unresolved P1/P2 finding. Live GPU
execution additionally requires published immutable job source and fresh
toolkit authority; neither is inferred from scaffold acceptance.
