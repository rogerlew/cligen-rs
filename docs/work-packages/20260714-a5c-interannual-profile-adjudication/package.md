# A5c Interannual Profile Adjudication

Status: `EXECUTED-COMPLETE`
Date: 2026-07-14
Evidence mode: Mixed (static adjudication; ran verification and repository gates)

## Objective

Apply ADR-0002 and SPEC-A5-EVALUATION to the accepted A5b evidence, record the
conservative no-promotion result, and close the ratified A5a–A5c sequence
without changing any public compatibility surface.

## Scope

Included: hash-lock the accepted authority, evidence, report, and public
surface; adjudicate all seven independently versioned candidates at both
horizons; record the evidence-access boundary; publish a human- and
machine-readable decision; verify that no candidate or interface was promoted;
and move A5c from the active roadmap to the work-package catalog.

Excluded: new climate generation, refitting, gate revision, candidate ranking,
production implementation, public schema revision, and A5d preregistration.

## Authority

- [ADR-0002](../../decisions/0002-quality-metrics-authority.md) makes the
  quality vector the extension authority.
- [SPEC-A5-EVALUATION](../../specifications/SPEC-A5-EVALUATION.md) requires all
  climate gates at both horizons before a candidate is eligible.
- [SPEC-A5B-CANDIDATES](../../specifications/SPEC-A5B-CANDIDATES.md) fixes the
  seven independent candidate/profile/model identities.
- The accepted A5b package and experiment report are frozen by
  [`artifacts/evidence-lock-v1.json`](artifacts/evidence-lock-v1.json).

## Plan

1. Freeze the accepted A5b evidence and current public profile surface.
2. Adjudicate every candidate/horizon row under the registered contract.
3. Record no promotion, unchanged independent version axes, and the prospective
   renewal condition in ADR-0004 and machine-readable form.
4. Run a fail-closed verifier, mutation self-tests, and repository gates.
5. Close the roadmap item and catalog the package.

## Execution & dispatch

Executed in the shared repository `/Users/roger/src/cligen-rs`, starting from
clean `main` at `8d00f8c2108910f257b29c02341c0e1fca9e4dd9`, with the repository's
default push target `main`. This package was not dispatched to another
executor and does not create a side branch.

The adjudication read the already accepted A5b and report artifacts; it did not
rerun the experiment or expose any new response surface. The verifier checks
the complete evidence lock, the 14-row results table, the accepted report
manifest, the exact candidate/model/profile mapping, the unchanged public
runspec enum/default, and the absence of A5b profile IDs from accepted public
surfaces.

## Gates

- `python3 artifacts/verify-a5c-decision.py`
- verifier mutation tests: duplicate key, evidence hash, candidate eligibility,
  promotion, public-surface mutation, and public-default mutation must fail
- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`

The coverage/CRAP gate is not triggered: A5c changes no production function in
`crates/`.

## Exit criteria

Complete when the immutable evidence verifies; all 14 candidate/horizon rows
are represented and ineligible; promoted candidate/profile lists are empty;
the exploratory boundary and prospective renewal condition are explicit; the
public default remains faithful; no compatibility schema changes; ADR-0004,
the roadmap, and the catalog agree; and all gates pass.

## Result

`NO-PROMOTION`. None of the seven candidate versions passed all climate gates
at both horizons. The accepted public surfaces and their independent versions
are unchanged. A renewed candidate requires a separate prospective study; the
A5b evidence cannot be used to rescue a candidate by post-hoc gate changes.

## Artifacts

- [`artifacts/evidence-lock-v1.json`](artifacts/evidence-lock-v1.json) — hashes
  of decision authority, accepted evidence, reviews, and public surfaces.
- [`artifacts/a5c-decision-v1.json`](artifacts/a5c-decision-v1.json) — canonical
  machine-readable disposition.
- [`artifacts/promotion-adjudication.md`](artifacts/promotion-adjudication.md) —
  human-readable finding and renewal condition.
- [`artifacts/verify-a5c-decision.py`](artifacts/verify-a5c-decision.py) —
  fail-closed verifier and mutation self-tests.
- [`artifacts/review.md`](artifacts/review.md) — closure review.
- [`artifacts/gate-results.md`](artifacts/gate-results.md) — executed commands
  and outcomes.
