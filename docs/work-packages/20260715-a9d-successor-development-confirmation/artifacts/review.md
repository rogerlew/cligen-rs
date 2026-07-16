# A9d consolidated internal review

Date: 2026-07-15
Internal-review report SHA-256:
`25bfec51344cc31e79e6c4dd5c517fc93f53bd15580161011427d4092343fafe`
Accepted report SHA-256:
`dde287fdd88d363b43894a041143ce6fc1cbc7cb3c6852c2f7cb37ea6160b34d`

The lead author applied every correction. Three independent read-only lenses
rechecked the exact internal-review hash and the final accepted hash and
returned `ACCEPT`. The accepted hash differs only by the required
`Status: ACCEPTED` metadata transition and a non-scientific clarification that
the claim ledger and review record have distinct roles.

## Lens coverage

### Accuracy — ACCEPT

The reviewer independently reproduced the 18 valid fits, 92/19 accepted
surface, 18/4/2 stage funnel, 24 staged configuration evaluations, 160
faithful runs, 720 strict context prefixes, 1,040 candidate engineering
attempts, replay summaries, three renewal and 17 latent degradation rows,
zero candidate freezes, resource totals, and final terminal. All 20 report
evidence hashes matched.

### Scientific validity — ACCEPT

The reviewer confirmed all six hypothesis dispositions; H3's amended
provenance; H2's partial strict-support scope; uncertainty-adjusted monthly
reconciliation language; family/horizon rather than campaign-wide threshold
scope; selection-conditioned result language; bounded class/panel conclusion;
and the unreached confirmation condition.

### Consistency and public safety — ACCEPT

The reviewer confirmed report, manifest, package, roadmap, and catalog
identities; local links; citations and DOI/URL identities; source-authority
language; runtime-field precedence; confirmation-period correction; absence
of target-series data, secrets, local paths, and unsafe copyrighted links;
coefficient-fit-only sources; zero roster overlap; and appropriate LFS scope.

## Findings and dispositions

| ID | Severity | Finding | Disposition | Recheck |
|---|---|---|---|---|
| A9D-METH-001 | P2 | Original closeout language obscured the pre-output withdrawal of occurrence calibration. | H3 is `amended`; report and package state amount-only calibration and preserve the access boundary. | ACCEPT |
| A9D-STAT-002 | P2 | A reconciliation pass could be misread as raw agreement within 0.5%. | Report gives raw maxima, the 3.290527× combined-SE allowance, and the deterministic-reexecution limit. | ACCEPT |
| A9D-STAT-003 | P2 | The campaign hold could be overgeneralized to a model-class rejection. | Conclusions are bounded to the grid, panel, surface, thresholds, stages, and burns. | ACCEPT |
| A9D-CONS-003 | P2 | Roadmap/catalog referenced a nonexistent prerequisite-only A9d package. | Phantom links were removed; operator supersession and the single actual A9d package are explicit. | ACCEPT |
| A9D-CONS-004 | P2 | Hash-bound runtime retained stale A9c3-derived grid, pooling, stage, terminal, and resource labels. | Canonical bytes remain unchanged; a hash-bound disclosure defines exact authority precedence and the report cites it. | ACCEPT |
| A9D-CONS-005 | P2 | The conditional confirmation fit endpoint conflicted with A9a by one day. | Pre-access correction restores the A9a-authoritative 2009-12-31 endpoint; confirmation was not reached. | ACCEPT |
| A9D-EVID-006 | P2 | Initial hypothesis crosswalk used the inherited runtime's H1--H4 rather than A9d H1--H6. | Ledger, report, and manifest disposition all six actual A9d hypotheses. | ACCEPT |
| A9D-EVID-007 | P2 | Strict event-context support covered short prefixes, not every later-stage stream in H2's quantifier. | H2 is partially supported; report distinguishes 720 strict audits from the inclusive 1,040-attempt validator. | ACCEPT |
| A9D-CONS-001 | P3 | Roadmap called A9c4 the latest successor after A9d closure. | A9c4 is labeled the predecessor completeness package. | ACCEPT |
| A9D-CONS-002 | P3 | Scientific notation rendered a literal TeX command. | Replaced with plain `× 10^-16` notation. | ACCEPT |
| A9D-ACC-001 | P3 | Reconciliation draw/path wording was multiplicatively ambiguous. | Now states two draws of 200,160 paths per fit each. | ACCEPT |
| A9D-ACC-002 | P3 | Pareto publication and lexicographic survivor ordering were conflated. | Report now states their actual order and conditional relationship. | ACCEPT |

## Mechanical and scientific gates

- A9d package verifier: PASS — 18 fits, 24 staged evaluations, 92/19
  surface, named hold.
- A9d unit tests: PASS — 4/4.
- Report internal-review verifier and self-test: PASS.
- Every published table and key narrative number independently reproduced:
  PASS.
- Hypothesis provenance, amendment history, missing-value policy, support
  scope, selector logic, and conclusion bounds: PASS.
- Public links, evidence identities, source authority, data boundary, and LFS
  scope: PASS.
- `git diff --check`, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test`: PASS.

Residual uncertainty is limited to what the accepted report states: incomplete
strict later-stage support audit, unretained candidate streams, the accepted
92-cell surface, two-site hot-arid storm construct, selection conditioning,
and absence of independent confirmation. No P3 finding remains open.

Final verdict: **ACCEPT**

Open P1: 0
Open P2: 0
