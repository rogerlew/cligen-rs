# A5e0 consolidated internal review

Status: `ACCEPTED`
Date: 2026-07-14
Report revision: 1
Reviewed report SHA-256: `3563ffe0c8d3a3a7f1d1d49ea059b22fcdb8d30e95fc6d69e70c332e9f59868b`
Campaign SHA-256: `ca810ec0bfb676fe045dd97bcc9efc9cb076e152f505c533097c5ca2415d16b2`

## Review method and coverage

The lead author dispatched three read-only reviewers before drafting: an
evidence/arithmetic analyst, a methods/scientific-validity analyst, and a
reference/public-safety analyst. The lead resolved their findings against the
repository artifacts, authored the report, and then applied all three required
review lenses to the hash-bound draft. Reviewers made no repository edits.

The accuracy lens independently checked:

- 144 fitted loadings and all recorded H0 thresholds;
- 48 unique primary runs, 96 arm/horizon cells, and all 288 indexed `.cli`,
  quality, and diagnostic identities;
- 48 formatted-row prefixes, candidate annual-state prefixes, and zero-bundle
  conformance;
- all 24 segment starts, 960 final faithful-stream states, canonical periods,
  and realized raw-update counts by independent modular replay;
- all 1,211 expanded metric bindings, family memberships, station ratios,
  horizon medians, and H1--H3 statuses; and
- both readings of the descriptor guard.

No arithmetic, hash, matrix, or reported-value disagreement remained. The
accuracy lens accepts the report's tables and narrative numbers.

The scientific-validity lens reconstructed the data boundary, coefficient
fit, generator seams, RNG partition, targets, aggregation, and decision
hierarchy. It found the prospective-boundary defect and four material H4
shortfalls. The report does not repair them: it classifies H0--H4 as
exploratory, distinguishes the provisional H1--H3 climate mapping from the
terminal campaign decision, and concludes with the evidence-integrity hold.
This is the only conclusion supported by the complete record.

The consistency/public-safety lens verified candidate/profile names, station
order, periods, horizons, run counts, source commit, implementation-commit
null state, package/catalog statuses, source-authority wording, DOI identity,
Daymet limitations, third-party notice, raw-data disposition, and the absence
of local copyrighted-PDF links or operator-specific absolute paths. It also
confirmed that no A5e0 LFS object is needed.

## Findings and dispositions

| ID | Severity | Finding and consequence | Disposition | Recheck |
|---|---|---|---|---|
| REV-A5E0-001 | P1 | The claimed freeze commit contains only the scaffold, not the exact spec, implementation, fitter, or analyzer. A formal prospective close is unsupported. | Accepted and central conclusion changed to `EXECUTED-HOLD-PROSPECTIVE-BOUNDARY`. No backdated freeze or formal `CLOSE-MECHANISM` claim remains. | Report metadata, hypothesis registry, Abstract, Results, Limitations, and Conclusions all use exploratory/hold language; campaign H4 is FAIL. |
| REV-A5E0-002 | P2 | Mandatory campaign evidence and H4 closure were missing. | Corrected with a strict campaign record and verifier binding the post-output tree, inputs, 48 runs, conformance products, analyses, and hold. | Campaign schema and `verify-a5e0.py --self-test` pass. |
| REV-A5E0-003 | P2 | Campaign hashes of report/review/gates would create a content-hash cycle. | Corrected by ending campaign evidence at analysis and letting the report manifest bind campaign and review. | No cyclic artifact identity remains. |
| REV-A5E0-004 | P2 | Spec and scaffold stated different descriptor aggregation rules. | Disclosed as a post-output authority mismatch; both readings were independently computed and pass. | Report publishes both readings and does not treat either as observational validation. |
| REV-A5E0-005 | P2 | The fitter's NumPy reductions, runtime derived-value intake, formatted-prefix check, and realized RNG count do not satisfy all stronger H4 wording. | Accepted as H4 failures; no outcome-time implementation repair, profile promotion, or production-readiness claim was made. | Campaign failure list, claim ledger, Methods, and Limitations agree. |
| REV-A5E0-006 | P2 | Same-product Daymet, mixed target authority, no-leap recurrence, three stress stations, and deterministic substreams constrain inference. | Corrected in claim scope. | Report avoids confirmation, independent-validation, station-truth, population, confidence-interval, and significance language. |
| REV-A5E0-007 | P3 | The analyzer used verified standalone 30-year prefix views rather than truncating 100-year files during scoring. | Clarified without changing values. | Report calls them deterministic prefix views; 48 formatted prefixes independently match. |
| REV-A5E0-008 | P3 | A generated A5b `__pycache__` directory appeared in the worktree. | Removed. | Final status contains no untracked Python cache. |

## Hypothesis and conclusion consistency

- H0 is reported as an exploratory analytic PASS, not a production
  coefficient qualification.
- H1 ratios reproduce exactly and fail at both horizons; all six station/
  horizon ratios exceed 1.0.
- H2 passes at 30 years and fails at 100 years only because the monthly family
  crosses its median limit.
- H3 passes under both descriptor readings and is correctly described as a
  guard, not validation.
- H4 fails, so the terminal package decision is the prospective-boundary hold
  even though the climate-only analysis maps H1--H3 to close.
- The conclusion leaves A5e1, confirmation, public promotion, and production
  coefficient use unauthorized and creates no automatic repair package.

## Residual uncertainty

- The exact pre-H0 and pre-campaign file hashes were not durably retained; the
  access chronology is disclosed but cannot be upgraded to an immutable
  preregistration.
- Raw campaign products remain local under ignored `target/a5e0/`; their 288
  identities were checked during this review but the public repository retains
  only the compact campaign manifest.
- The Python numerical environment is version-recorded but not fully locked to
  a BLAS/LAPACK build.
- Daymet product dependence, no-leap normalization, purposive station
  selection, and absence of confirmation/downstream evidence limit scientific
  generalization.

Final verdict: **ACCEPT**

Open P1: 0
Open P2: 0
