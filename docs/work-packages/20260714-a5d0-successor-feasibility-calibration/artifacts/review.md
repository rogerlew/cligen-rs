# A5d0 Consolidated Internal Review

Verdict: `ACCEPT`
Review date: 2026-07-14
Review mode: three independent read-only lenses; lead-only dispositions
Open findings: P1 `0`, P2 `0`, P3 `0`

## Scope and method

The scientific-report authoring protocol was applied proportionally to this
feasibility package. The lead froze inputs and authored the artifacts. Three
read-only reviewers independently examined accuracy, scientific validity, and
consistency/public safety. Reviewers did not edit files. The lead applied all
corrections, then the originating reviewer performed bounded rechecks for every
P2 and the affected P3/spectral disposition.

This is not acceptance of an A5d candidate. It is acceptance that the package
correctly and reproducibly closes `HOLD-CONTRACT-INCOMPLETE`, with independent
secondary evaluation and corpus holds.

## Lens 1 — accuracy

Verdict: `ACCEPT`; no findings.

The reviewer independently reproduced:

- total fixture variance `13/3`;
- between-year variance `5/3 -> 7/3` (+40%);
- mean within-year variance `8/3 -> 2` (−25%);
- equal absolute variance reallocation `2/3` and zero changed daily values;
- lag-one covariance `7/5 = 1.4`;
- same-block probability `61/90 = 0.677777...`;
- zero-frequency ratio `(1 + 0.6) / (1 - 0.6) = 4`;
- one-sided zero-failure upper bounds after 8 and 59 trials;
- exact sign designs 23/16 and balanced 28/19;
- all 19 input hashes, 17 Daymet and eight GHCN identities, and revision-3
  bootstrap availability 221/2,000 and 8/2,000.

The fixture script reproduced the stored JSON byte-for-byte and its self-test
passed.

## Lens 2 — scientific validity

Initial verdict: `ACCEPT WITH CORRECTIONS` (no P1). Final verdict: `ACCEPT`.

| ID | Severity | Finding and consequence | Disposition | Recheck |
|---|---|---|---|---|
| A5D0-SV-001 | P2 | Toy counterexample and repeat probability were framed as the reason `GO` failed, although neither disproves actual-library feasibility and no reuse ceiling existed. | Reframed them as cautions. The blocker is now the missing actual-library solution, bounded repeat-safe path, and prospectively adjudicated reuse ceiling. | RESOLVED |
| A5D0-SV-002 | P2 | The 28/19 independent sign design was called a powered confirmation minimum despite missing spatial/composite/regime power. | Relabeled 28 as a provisional sign-test planning floor; follow-on calibration must determine the actual minimum. | RESOLVED |
| A5D0-SV-003 | P2 | Displayed moment constraints silently assumed equal block length. | Declared the fixture assumption and added block/day- and month-count-weighted production constraints with separate annual-total treatment. | RESOLVED |
| A5D0-SV-004 | P3 | Lag-one covariance alone did not establish low-frequency power. | Added `P^k`, the complete autocovariance identity, and the zero-frequency spectral ratio, plus a reproduced fixture field. | RESOLVED |

The reviewer confirmed the revised fixture still reproduces byte-for-byte and
found no new scientific-validity issue.

## Lens 3 — consistency and public safety

Initial verdict: `ACCEPT WITH P3 CORRECTIONS`; one interim P2 was resolved by
the completed verifier. Final verdict: `ACCEPT`.

| ID | Severity | Finding and consequence | Disposition | Recheck |
|---|---|---|---|---|
| A5D0-CONS-001 | P2 | The initial draft indirectly relied on the A5c public-surface lock without an A5d executable check. | The A5d verifier now validates all ten nested hashes, exact public enum/default, absence of A5d public IDs, and absence of a held-package normative spec. | RESOLVED |
| A5D0-CONS-002 | P3 | Inventory used `cold_snow` where the accepted climate-regime token is `cold`. | Changed to `cold` and explicitly distinguished the downstream WEPP cold/snow-domain taxonomy. | RESOLVED |
| A5D0-CONS-003 | P3 | The package embedded an operator-specific absolute repository path. | Replaced it with portable “repository root on `main`” wording. | RESOLVED |

The reviewer also confirmed agreement on fit/evaluation periods, horizons,
research-only status, A5c authority, faithful default, clean exposure, terminal
hold, and zero production/specification/schema changes.

## Closure assessment

PASS:

- The decision follows the package's fail-closed exit criteria.
- No fixture is represented as confirmation or actual-library evidence.
- All numeric statements are reproducible from machine evidence.
- The lack of an actual selector, calibrated evaluation, WEPP rule, and
  untouched corpus is explicit rather than papered over.
- No candidate ID or public compatibility surface is created.
- No confirmation candidate/target value was accessed.
- Every P2 and P3 finding is resolved and rechecked; no residual review finding
  remains open.

Residual uncertainty is the subject of the terminal hold, not an unreviewed
defect: the complete constraint system may or may not be feasible on real
faithful development libraries, and evaluation/corpus calibration remains to
be executed prospectively.
