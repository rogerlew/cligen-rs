# Interannual Candidate Experiment 001 Report

Status: `EXECUTED-COMPLETE`
Date: 2026-07-14
Evidence mode: Mixed

## Objective

Establish a reusable scientific-report standard, template, multi-agent
authoring protocol, and comprehensive consistency gates, then apply them to a
public report of the completed A5b interannual candidate experiment.

## Scope

Included: report governance under `docs/standards/`, a report catalog and
template, a strict manifest verifier, an A5b claim-evidence ledger, the
`interannual-candidate-exp-001` report, independent accuracy/method/reference/
consistency lenses, and recorded repository gates.

Excluded: rerunning A5b, changing its evidence, promoting a candidate,
modifying faithful generation or production code, and making an A5c decision.

## Authority

- Report structure and acceptance are governed by the new version-1 report
  standard and authoring protocol.
- A5b methods and results remain governed by `SPEC-A5B-CANDIDATES` revision 1,
  `SPEC-A5-EVALUATION` revision 3, and the accepted A5b work package and
  canonical analyses.
- Faithful-mode authority remains the vendored Fortran under ADR-0001.

## Plan

1. Freeze scope, canonical evidence, claim classes, and source commit.
2. Dispatch independent read-only standards, evidence, and reference audits.
3. Implement the standard, protocol, template, manifest, and mechanical gate.
4. Author the report from the reconciled claim-evidence ledger.
5. Dispatch independent accuracy and consistency reviews, disposition findings,
   and perform bounded rechecks.
6. Run all report and repository gates, update catalogs, and close honestly.

## Outcome

The version-1 scientific report standard, multi-agent authoring protocol,
template, strict manifest verifier, report catalog, and A5b experiment report
are complete. The accepted report preserves the exploratory access boundary,
publishes the full climate and WEPP result tables, and concludes that none of
the seven exact A5b candidates is eligible for promotion.

Three independent review lenses recomputed the evidence and produced one
accuracy, six scientific-validity, and six consistency/public-safety findings
on the initial draft. The lead dispositioned every finding; bounded rechecks
accepted all corrections with zero open P1/P2/P3. The final report and review
are hash-bound by the manifest, all report/repository/LFS gates pass, and no
new large artifact requires Git LFS.

After initial acceptance, an operator-requested advisory review identified five
prospective gate-calibration and successor-design improvements. Report revision
2 incorporates all five with explicit qualifications, corrects the advisory's
approximate dewpoint-cap rate to 34.4% from exact row counts, and retains every
experiment table, hypothesis outcome, and no-promotion decision.

## Execution & dispatch

Execution starts on `main` at `/Users/roger/src/cligen-rs` and targets `main`.
Subagents are read-only and may not edit, commit, or push. The lead author is
the only editor. No branch is created.

## Gates

- `python3 docs/reports/verify-report.py --self-test`
- `python3 docs/reports/verify-report.py docs/reports/interannual-candidate-exp-001-report.manifest.json`
- independently recompute every published quantitative table;
- validate report/evidence hashes and Git LFS integrity;
- complete accuracy, scientific-validity, and consistency/public-safety lenses;
- zero open P1/P2 review findings;
- `git diff --check`
- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`

Coverage/CRAP gates do not apply because this package changes no production
function under `crates/`.

## Exit criteria

`EXECUTED-COMPLETE` requires an accepted report and manifest, passing
mechanical/scientific/consistency gates, an accepted consolidated review with
no open P1/P2 findings, and updated report/work-package catalogs. A material
evidence contradiction closes as `EXECUTED-HOLD-EVIDENCE`; a failed public-
safety review closes as `EXECUTED-HOLD-PUBLIC-SAFETY`.

## Artifacts

- `artifacts/claim-evidence-ledger.md` — frozen claims and evidence mapping.
- `artifacts/review.md` — consolidated independent lenses and dispositions.
- `artifacts/post-acceptance-advisory-review.md` — operator-requested
  prospective gate and successor-design review.
- `artifacts/gate-results.md` — exact commands and terminal results.
