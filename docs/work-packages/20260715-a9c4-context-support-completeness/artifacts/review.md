# A9c4 consolidated internal review

Status: `ACCEPTED`
Date: 2026-07-15
Report: `docs/reports/a9c4-context-support-completeness-report.md`
Final internal-review report SHA-256:
`ee112cf0385c092a5dcd2c7ef52768e2bdfe76ec9ed6139ca8206b2347722114`
Accepted report SHA-256 after the status-only transition:
`436e6590222f751914079e193dfa7374c13562c03466440a6330f2c49f9b2720`

## Scope and protocol

The lead froze E01--E12 before drafting, then appended E13 after independent
evidence extraction found the historical storm-count/status evidence boundary.
Three read-only roles independently extracted numeric evidence, methods, and
reference/data authority. The lead alone drafted and corrected the report.
The strict internal-review verifier passed before final lens dispatch.

The initial internal-review report hash was
`38cc32fe803978f06837222bf6bfcfd41d2932b39353c2475b5115dc83e2ba6e`.
After SCI-001 and CON-001--CON-003 it was
`631d734e7d7925b16cd71689e7d6da3c1427861b676665a3c7d90c4266e5537e`.
After ACC-001--ACC-003 and their ledger dispositions it reached the final
internal-review hash above. Every lens accepted that hash.

## Pre-draft extraction and deviation disposition

Independent extraction reproduced the 111-cell partition, family/regime
arithmetic, breadth failure, predecessor hashes, and terminal. It also found
that the audit's historical storm rows were not measured like non-storm rows:
144 storm statuses were copied from accepted A9c3 policy, and 96 stored storm
contributor counts used the generated-contributor count where A9c3 stored the
observed-group count. The lead recorded E13 before drafting. The corrected
report claims 522 recomputed non-storm statuses, 144 inherited storm statuses,
and 96 count-label discrepancies. No status, mask cell, breadth result, or
terminal changes.

The first audit execution wrote its canonical audit, then hit a Python Boolean
token error during mask construction. E06 records the deterministic closeout
from the unchanged audit and frozen rule. No corrected A9c4 output existed at
either boundary.

## Lens results

### Accuracy

Final verdict: `ACCEPT` after corrections.

The reviewer independently verified all 13 evidence hashes, all three
governance hashes, the 11 predecessor identities, 111 unique cell keys, the
92/19 partition, family and regime tables, 68/24 retention decomposition,
522/144 historical-status evidence split, 552/114 stored totals, 96 count-
label discrepancies, six breadth failures, hypotheses, study facts, and the
terminal. The package verifier passes.

### Scientific validity

Final verdict: `ACCEPT` after correction.

The reviewer accepted the candidate-blind access boundary, non-storm common-
support rule, grouped-storm policy exception, hypothesis outcomes, early stop,
bounded confirmation claim, and limitations. The corrected conclusion closes
A9c4 at the hold and requires any evidence-scope change to be prospectively
frozen under a separately identified successor; H1 cannot be relabeled.

### Consistency and public safety

Final verdict: `ACCEPT` after corrections.

The reviewer verified source commits, product/version/period scope, DOI/URL
identities, ADR authority boundaries, local links, LFS integrity, provider
notices, and exact package/report terminology. Python bytecode caches are
ignored and no new cache containing operator paths is staged. No secret,
credential, private key, operator-specific absolute path, local-file URI, or
copyrighted reading-copy link appears in public authored artifacts.

## Findings and dispositions

| ID | Severity | Finding | Disposition | Recheck |
|---|---|---|---|---|
| SCI-001 | P2 | The conclusion could be read as retrospectively overriding A9c4's failed breadth guard. | Closed A9c4, prohibited relabeling H1, and required a separately identified prospective successor for any evidence-scope change. | Scientific-validity recheck `ACCEPT`. |
| ACC-001 | P2 | Abstract/results described all 92 retained cells as common-support tested although 24 storm cells were policy-retained. | Report now states 68 non-storm common-support plus 24 grouped-policy storm cells. | Accuracy recheck `ACCEPT`. |
| ACC-002 | P2 | Report described all 666 stored historical statuses as recomputed although 144 storm statuses were copied. | Report and E12/E13 now state 522 recomputed non-storm plus 144 inherited storm statuses. | Accuracy recheck `ACCEPT`. |
| ACC-003 | P2 | `Absent` overstated four excluded cells having one observed contributor. | Report now says all 19 lacked the required two contributors and gives the 15-zero/four-one split. | Accuracy recheck `ACCEPT`. |
| CON-001 | P3 | Inherited USCRN citation omitted exact subset identity and network attribution. | Restored Subhourly01 format/OAP scope and Diamond et al. R04. | Consistency recheck `ACCEPT`. |
| CON-002 | P3 | Package/roadmap overstated A5b-specific ADR-0004 as general promotion authority. | Restored ADR-0002 general authority and limited ADR-0004 to A5b no-promotion/no-rescue. | Consistency recheck `ACCEPT`. |
| CON-003 | P3 | Generated Python bytecode caches contained operator-specific paths. | Removed new caches and added repository ignore rules for cache/bytecode files. | Consistency recheck `ACCEPT`. |

## Scientific and consistency gates

- PASS — exact report facts and tables reproduce from E04, E05, E07, and E13.
- PASS — unavailable cells retain explicit report-only roles and no favorable
  score.
- PASS — storm-policy rows are separated from non-storm common-support rows.
- PASS — recomputed statuses are separated from inherited statuses and count
  labels.
- PASS — H1 is not supported; H2--H4 are not evaluated; H5 is a bounded code-
  path claim.
- PASS — no corrected A9c4 fit, output, evaluation, selector, or freeze is
  claimed.
- PASS — the exact hold is consistent across mask, report, package, catalog,
  and roadmap closure.
- PASS — LFS and provider/copyright boundaries remain public-safe.

## Residual uncertainty

- The audit retains no per-burn historical candidate features or output
  hashes; independent feature recomputation requires deterministic rerun.
- Storm availability/status is inherited policy evidence rather than an
  independent feature-support measurement.
- The 30-year, two-burn audit does not establish later-stage availability.
- The proposed log/logit context transforms, exact-zero behavior, epsilon
  sensitivity, and numerical support remain untested.
- A9c3's degradation rows, full development, replay, confirmation, runtime,
  and integration remain unresolved.

Final verdict: **ACCEPT**

Open P1: 0
Open P2: 0
