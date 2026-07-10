# Q3 — `qc_filter` Implementation + Dissection + Exposure Adjudication

Status: `EXECUTED-AWAITING-OPERATOR-ADJUDICATION` — pre-registration
ratified; observed reference acquired; `qc_filter` implemented
(SPEC-RUNSPEC rev 5, metrics_version 2 counterfactuals); 102-run
matrix executed and analyzed against the pre-registered bounds
(`artifacts/frontier-analysis.md`); **ADR-0003 drafted as Proposed**
— the exposure ruling is the operator's.
Date: 2026-07-10
Evidence mode: **Ran** (`artifacts/gate-results.md`)

## Objective

Close ROADMAP Q3 under ADR-0002: implement the `qc_filter: faithful |
off` conditioning knob (SPEC-GENERATION-PROFILES rev 3 semantics —
faithful default preserves the goldens; `off` skips only the
accept/retry loop and its QC accumulation while emitting group-P
counterfactual verdicts), run the **pre-registered** dissection
matrix, quantify the convergence-vs-variability frontier per horizon,
re-baseline performance against qc_off, and put the exposure question
to the operator as ADR-0003.

## Order of work (the pre-registration discipline)

1. **Pre-registration ratified first** —
   `artifacts/pre-registration.md` (DRAFT now): corpus, observed
   reference, metrics, bounds, and decision rules on the record
   before any dissection run.
2. Observed-reference acquisition (python campaign tooling in
   artifacts; committed derived statistics + pinned raw hashes).
3. `qc_filter` implementation + SPEC-RUNSPEC/schema rev (same-change
   discipline) + counterfactual group-P surface (the Q1 C-R1-003
   deferred decision: metrics-version consequence is decided here).
4. Dissection runs; reports archived; frontier quantified.
5. ADR-0003 (operator adjudication); package close.

## Scope guards

- Faithful golden byte identity inviolate under the default.
- The quality module remains observation-only; the knob toggles the
  generation-side retry loop exactly as SPEC-GENERATION-PROFILES
  rev 3 defines.
- Observed-data comparison lives in this package's adjudication
  artifacts, never in the report emitter (SPEC-QUALITY-REPORT
  non-goal).
- `fast_batch_v1` remains out of scope (Q4).

## Artifacts

- `artifacts/pre-registration.md` — RATIFIED, bounds pinned pre-run.
- `artifacts/observed/` — acquisition tooling + derived statistics
  (Daymet primary, GHCN secondary), raw hashes pinned.
- `artifacts/run-matrix.py`, `runs.json`, `analyze-matrix.py`,
  `matrix-analysis.json`, `timing-no-sidecar.json` — the campaign.
- `artifacts/frontier-analysis.md` — verdicts vs the bounds.
- `artifacts/gate-results.md` — Ran gates.
- `docs/decisions/0003-qc-filter-exposure.md` — Proposed.
- `artifacts/review-codex.md` / `artifacts/disposition-claude.md` —
  the R1 review cycle (8 findings, 8 accepted; two HIGH corrections
  applied to the adjudication record; Codex's independent opinion:
  ratify ADR-0003 as amended, retire fast-batch on portfolio grounds).
- `artifacts/estimator-sensitivity.json` — R1 findings 1/4
  remediation computations.
- Evidence archive: release `q3-evidence-2026.07`
  (`q3-matrix-evidence.tar.gz`, sha256 cc42e65e…8072a).
