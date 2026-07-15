# A7a consolidated internal review

Status: `ACCEPTED`
Date: 2026-07-14
Report revision: 1
Reviewed report SHA-256: `1ebece39de2b1528eec91c76b5067c9000c8b600de9ab68821b853e9b1774bc4`
Canonical analysis SHA-256: `45342c8763c3d079c81f8a9b3910882bdd82f2557dfb420a80d5a4bfefa2b1ad`
Canonical decision SHA-256: `c5aab286d5fffb8a61bb3bb50ac228f636d6da97f6e0880973f478073e0b1c0f`

## Review method and coverage

The lead author dispatched three read-only roles under the scientific-report
protocol: an evidence/arithmetic analyst, a methods/scientific-validity
analyst, and a reference/consistency/public-safety analyst. They edited no
repository file. The lead resolved findings against the frozen contract,
canonical metrics, parent manifests, official dataset records, and faithful
source-authority decision, then each lens rechecked its P1/P2 dispositions.

The accuracy lens independently regenerated all 700 comparison rows directly
from persisted generated and observed metric vectors. It reproduced all
observed distances, leave-one-trajectory-out ceilings, component counts,
directions, material flags, and severity encodings; all 56 summaries; all five
pooled rank severities; all ten QC comparisons; and all four propagation rows.
It verified 625 finite severity ratios, 55 positive-over-zero `"infinity"`
values, 11 zero-over-zero `0.0` values, and nine unavailable/null values. It
also verified the freeze chain, output hashes, matrix dimensions, overlap-
check arithmetic, table rounding, qualifying families, and terminal decision.

The scientific-validity lens reconstructed populations, calendars, nested
horizons, deterministic-burn interpretation, daily-family definitions,
minimum-component rules, null, breadth guards, amendment access boundaries,
QC and propagation diagnostics, and conclusion scope. It accepted the final
report only after H3/H4 used the amended ledger's descriptive wording, the
zero-null severity was distinguished from physical infinity, calendar and
observed-length threats were explicit, and A7a no longer selected an A7b
mechanism or predicted success.

The consistency/public-safety lens verified versions, station/source counts,
periods, profile, reference metadata, DOI/URL identities, official Daymet
calendar behavior, GHCN shared lineage and non-homogenization scope, stable
reference IDs, local links, source authority, third-party notice, non-LFS
claims, ignored copyrighted reading copies, and absence of private or
operator-specific links. Reference-corpus amendment 006 preserves frozen R04
and adds audited R05/R06 identities without rewriting access history.

## Findings and dispositions

| ID | Severity | Finding and consequence | Disposition | Recheck |
|---|---|---|---|---|
| A7A-CALC-001 | P2 | The first analysis ranked severity as the median of two horizon medians rather than the frozen pooled station-horizon median. | Post-analysis amendment 005 changed the reducer to all available Daymet-off station-horizon cells and preserved the exposed first-output hashes. | Accuracy lens independently reproduced all five corrected pooled values; rank and terminal remain unchanged. |
| A7A-CALC-002 | P2 | Available zero-null cells were omitted from severity, leaving the ranking denominator undefined. | Amendment 005 defines positive/zero as JSON string `"infinity"` and zero/zero as `0.0`; unavailable remains null. | All 66 zero-null cells and the 34-cell Daymet-off spell pool independently reproduce. |
| A7A-CALC-003 | P2 | Two GHCN Death Valley 100-year occurrence nulls used 15 generated-only components while observed distance used 13. | Amendment 005 restricts every null to the corresponding observation-supported component set and records min/max support. | All 700 observed/null component counts match; the two corrected flags are material, and the limiting 30-year breadth and terminal are unchanged. |
| A7A-ACC-001 | P2 | The internal draft referred to final package/review/gate records before closure. | Package, review, gates, report, roadmap, and catalogs were closed together and their final hashes entered the accepted manifest. | Final report and package verifiers pass; all referenced records are populated and accepted. |
| A7A-ACC-002 | P3 | H2 shorthand omitted the separately ordered Daymet-off, faithful, and GHCN-off breadth keys. | The hypothesis row now enumerates all three minima before severity and identifier. | Accuracy recheck accepts the registered rule wording. |
| A7A-ACC-003 | P3 | Draft file sizes used binary-rounded values with decimal MB labels and cited the freeze rather than the canonical JSON. | Numeric sizes were removed; the report states only verified storage behavior and cites the canonical artifact. | `git check-attr`, `git lfs ls-files`, and file identity checks pass. |
| A7A-SV-001 | P2 | The draft conclusion selected an occurrence/spell mechanism beyond A7a authority. | The conclusion now says A7b may evaluate motivated mechanisms, while A7a neither selects one nor predicts success. | Scientific-validity recheck accepts the conclusion and abstract scope. |
| A7A-SV-002 | P3 | The draft called eight monthly/annual Spearman coefficients “four associations.” | Corrected to eight coefficients. | Values and wording match all four horizon/QC records with two coefficients each. |
| A7A-SV-003 | P3 | The Daymet transform discussion omitted the generated/GHCN Gregorian calendars. | Added proleptic-Gregorian comparison calendars and treated the mismatch as a construct threat. | Scientific-validity recheck accepts the self-contained limitation. |
| A7A-CPS-001 | P2 | The first draft reassigned frozen R04 from the Menne overview article to the GHCN dataset and added sources without an amendment. | Reference-corpus amendment 006 preserves R04 and adds R05/R06; report and manifest use one stable mapping. | Reference recheck confirms exact ID/citation/DOI agreement. |
| A7A-CPS-002 | P3 | Draft dataset citations omitted formal title, subset, and access qualifiers. | R03/R05 now include formal product title/version, archived subset, provider, and 2026-07-12 access date. | Reference recheck accepts metadata against the third-party notice and official records. |
| A7A-CPS-003 | P3 | Draft LFS prose repeated the ambiguous MB values. | The final report omits the sizes and retains only verified Git/LFS facts. | Consistency/public-safety recheck accepts with no new finding. |

## Hypothesis and conclusion consistency

- H1 is amended and supported only under the operational breadth rule; it is
  not a population-significance statement.
- H2 is a deterministic ranking under the exposed matrix; its stability is
  not tested.
- H3 reports eight positive associations and joint-material counts without a
  causal or pass/fail interpretation.
- H4 reports directional QC-arm comparisons without a materiality bound.
- `spell_structure` and `higher_order_occurrence` qualify at both horizons,
  yielding `DAILY-PRECIPITATION-GAP-MEASURED`.
- The terminal permits a separately dispatched analytic feasibility package;
  it selects no mechanism and predicts no candidate success.

## Residual uncertainty

- The contract phrase “3 significant decimals” is terminologically ambiguous.
  The public report uses three significant figures for severity and three
  decimal places for correlations; the generated concise findings retain
  three fixed decimal places. Exact binary64 values remain canonical.
- Richardson full text was not part of the local review corpus, so the report
  uses only publisher-supported Markov-chain context and does not assign exact
  CLIGEN mechanics to that paper.
- The mutable Daymet Version 4.1 and GHCN Version 3 products are identified by
  the archived access date and hashes; the GHCN three-part build code was not
  captured and is not inferred retroactively.
- The deterministic eight-trajectory null, purposive stations, unequal record
  lengths, shared source lineage, and calendar transform bound inference as
  stated in the report.

Final verdict: **ACCEPT**

Open P1: 0
Open P2: 0
