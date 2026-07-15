# A5e0 claim and finding ledger

Status: `FROZEN-FOR-REPORT`
Date: 2026-07-14
Evidence mode: Mixed

## Independent extraction

The lead author dispatched three read-only roles before drafting: evidence and
arithmetic, methods and validity, and references and public safety. The lead
alone edited repository files. All three roles identified the false freeze-
commit claim; both scientific roles classified it as decision-invalidating.

| Claim | Class | Accepted evidence | Accepted wording |
|---|---|---|---|
| H0 feasibility | Ran/Derived | coefficient bundle and feasibility record | All recorded analytic budgets passed, but H0 is exploratory because the exact fit contract was not immutably sealed before access. |
| Matrix closure | Ran/Derived | matrix index, 288 products, campaign record | 48 primary runs and 96 arm/horizon cells were produced; all indexed hashes recomputed. |
| RNG partition | Derived | diagnostics and independent modular replay | Realized starts, ends, paired states, periods, and update counts replayed; the prospective conservative segment proof was not supplied. |
| H1 | Derived | canonical analysis | Failed at 30 and 100 years; all three station ratios exceeded 1.0 at both horizons. |
| H2 | Derived | canonical analysis | Passed at 30 years and failed at 100 years on the monthly-station-contract family. |
| H3 | Derived | canonical analysis and post-output audit | Passed under both the committed-scaffold composite and literal-spec subfamily readings; this is not observational storm validation. |
| Terminal disposition | Interpretation governed by evidence | campaign record | `EXECUTED-HOLD-PROSPECTIVE-BOUNDARY`; the analysis artifact's `CLOSE-MECHANISM` is only a provisional H1--H3 mapping. |

## Findings and dispositions

| ID | Severity | Finding | Disposition | Recheck |
|---|---|---|---|---|
| A5E0-001 | P1 | The named execution-base commit contains the scaffold, not the exact spec, fitter, implementation, or analyzer; no immutable pre-output hash sealed them. | Accepted. Reclassified H0--H3 as exploratory and set the terminal package decision to `EXECUTED-HOLD-PROSPECTIVE-BOUNDARY`. The false freeze label was removed; no backdated freeze was created. | Campaign and report must state the hold and leave A5e1 unauthorized. |
| A5E0-002 | P2 | The mandatory campaign record and H4 closure were absent. | Corrected. A strict campaign record now binds the post-output implementation tree, inputs, 48 runs, conformance products, analysis, and hold. | `verify-a5e0.py --self-test` passes. |
| A5E0-003 | P2 | Campaign-to-report hashes formed a cycle. | Corrected. Campaign evidence now terminates at analysis; the report manifest binds campaign and review. | Both JSON schemas validate. |
| A5E0-004 | P2 | Descriptor thresholds were specified once per subfamily and once on their equal-weight composite. | Disclosed and audited post-output. Both readings pass at both horizons; neither changes the hold. | Independent arithmetic and `a5e0-descriptor-rule-audit-v1.json` agree. |
| A5E0-005 | P2 | The fitter used NumPy reductions where the spec stated chronological `math.fsum`. | Accepted as an H4 failure. Coefficients were not refit after outcome access and receive no production authority. | Report must not claim byte-conformance to the stated fit arithmetic. |
| A5E0-006 | P2 | Runtime intake trusts occurrence/amount derived claims instead of reconstructing all of them. | Accepted as an H4 failure. The research API is not promoted or exposed through a public profile. | Report and package must retain research-only status. |
| A5E0-007 | P2 | Prefix evidence compares formatted daily rows, and the conservative RNG consumption proof was replaced by realized counts. | Accepted as H4 failures. Exact formatted prefixes and all realized stream counts still replay, but the stronger names are not claimed. | Report uses `formatted-row prefix` and `realized update` wording. |
| A5E0-008 | P2 | The fit recurrence is no-leap while the generator emits Gregorian leap days. | Accepted as a construct limitation. | Report limits exact analytic preservation to the no-leap fitting recurrence. |
| A5E0-009 | P3 | The analyzer reads verified standalone 30-year outputs rather than truncating the 100-year files itself. | Clarified. Standalone outputs are deterministic prefix views whose formatted rows match the first 30 years in all 48 pairs. | No numeric effect. |
| A5E0-010 | P3 | A stale A5b Python cache appeared in the worktree. | Remove before handoff. | `git status --short` contains no cache path. |

## Residual uncertainty

- Daymet fitting and evaluation periods are temporally disjoint but belong to
  the same exposed gridded product.
- Three purposive stress stations and eight deterministic substreams do not
  support population inference, confidence intervals, or significance claims.
- The A5a no-leap normalization is not Daymet's official civil calendar.
- No GHCN, PRISM, gridMET, WEPP, or confirmation object was evaluated.
- Raw campaign files remain under ignored `target/a5e0/` and are not public
  repository artifacts.
