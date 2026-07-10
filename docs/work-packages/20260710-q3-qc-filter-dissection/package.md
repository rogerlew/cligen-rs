# Q3 — `qc_filter` Implementation + Dissection + Exposure Adjudication

Status: `SCAFFOLDED` — pre-registration DRAFT awaiting operator
ratification (corpus + observed-reference design proposed 2026-07-10)
Date: 2026-07-10
Evidence mode: — (per stage at execution)

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

- `artifacts/pre-registration.md` — DRAFT (this scaffold).
- Later: acquisition tooling + observed statistics, dissection run
  archive, frontier analysis, ADR-0003, review cycle.
