# A10 Study Plan Independent Review and Disposition

Status: `ACCEPTED — OPERATOR-AMENDED PACKAGE TOPOLOGY`
Date: 2026-07-16
Review target: commit `0ed827f8d0b7ffea025aa989a57aeee2646d8668`
Dispositioned plan SHA-256:
`f884b4a0566d57f27d63b6b40b07441541f7829126de9baf22a8b771bfc6ff06`
Reviewed document: [A10 study plan](a10-study-plan.md)

## Verdict

**ACCEPT after corrections.** No P1 finding was raised. The independent review
found six initial P2 findings and seven P3 findings. A bounded disposition
recheck found three additional P2 terminal-flow findings, the primary agent
added one P2 milestone-state finding, and the final bounded recheck found one
P2 target-access-state edge. Every finding was accepted, corrected, and
rechecked. Final open counts are:

- P1: 0;
- P2: 0; and
- P3: 0.

The corrections do not reverse the A10 pivot, change faithful-mode authority,
authorize production integration, access confirmation target values, or add
another work package. They made the then-existing single-package study
executable and prospectively testable.

## Post-review operator amendments

The review target, commit, and SHA-256 above remain the immutable identity of
the plan version the independent reviewer accepted. They do not claim byte
identity with later operator amendments.

On 2026-07-16, after observing that the A9 campaign had accumulated too many
ad hoc corrective packages, the operator replaced A10's monolithic package
topology with one cohesive package per planned milestone: `A10M0` through
`A10M9`. This supersedes the review's statements that all milestones live in
one package. It does not change milestone order, hypotheses, data roles,
selector semantics, confirmation access, resource ceiling, or production
scope. Ordinary iteration remains inside its owning milestone package, and a
hold does not automatically authorize a suffixed rescue package. Every
milestone package receives its own dispatch, evidence, review, terminal, and
immutable downstream handoff.

The same-day operational amendment also recorded the supervised MFA/SSH
bootstrap and the `rmm` orchestration environment. A live Lemhi preflight then
superseded stale public infrastructure details: I-CREWS access is exposed
through the group-restricted `gpu-icrews` partition; `node03` reports four L40
GPUs, `node04` reports four RTX A6000 GPUs, and the alternate module tree
offers CUDA 12.8 and Python 3.11.11. These are operational observations to be
reproduced and sealed by A10M2, not retrospective claims by the original
reviewer.

The original scientific review remains accepted. Each milestone package must
review its local design and its predecessor handoff before execution; package-
topology and live-environment changes are not silently attributed to the
original independent review.

## Review independence and method

The primary agent dispatched an independent subagent, `a10_plan_review`, to
review the committed plan without editing it. The reviewer was asked to test:

- scientific-method validity and fidelity to accepted A7--A9 evidence;
- corpus roles, leakage boundaries, calendars, and third-party-data controls;
- model/ablation identities and causal interpretation;
- applicability, fallback, selector, and confirmation-firewall semantics;
- GPU/Slurm realism and offline/restart requirements;
- the exact 5× warning and 10× stochastic-generation failure rule;
- milestone ordering, terminal completeness, and autonomous execution; and
- agreement with `AGENTS.md`, ADRs, the roadmap, and accepted benchmark
  conventions.

The reviewer read the complete plan and relevant local authorities, reproduced
the A9d development verifier, checked every local Markdown link, and verified
current GPU claims against official C3+3 and NVIDIA sources. The reviewer made
no repository change. The primary agent independently verified and
dispositioned the findings, edited the plan, and returned each correction set
to the same reviewer for bounded recheck.

Severity follows the repository convention:

- **P1:** central decision is false, unsafe, or materially unsupported;
- **P2:** material scientific, operational, traceability, or consistency defect
  requiring correction before dispatch; and
- **P3:** useful precision or coverage correction that does not overturn the
  central decision.

## Initial findings and dispositions

| ID | Severity | Finding | Disposition and correction | Recheck |
|---|---|---|---|---|
| A10-REV-001 | P2 | Cold-start time was combined with warm stochastic generation under the operator's 5×/10× rule, changing the requested estimand. | **Accepted.** The relative rule now applies only to warm stochastic generation. Cold start, initialization, serialization, RSS, and model size are separately reported deployment diagnostics governed only by prospectively frozen absolute safeguards. | `ACCEPT` |
| A10-REV-002 | P2 | The selector did not explicitly require improvement over both faithful B0 and renewal B1 despite the primary question and H5. | **Accepted.** M3 now freezes paired common-cell differences `D0` and `D1`, positive material-improvement thresholds, and noninferiority guards. Regime applicability requires improvement over both baselines at both horizons. | `ACCEPT` |
| A10-REV-003 | P2 | The original no-pooling ablation was ambiguous and could not generate coherently at held-out stations. | **Accepted.** N0 is now an executable complete-pooling, transferable-descriptor-only model. N1 is the otherwise identical hierarchical partial-pooling model with regularized fit-station deviations and a prior/global-regime rule for unseen stations. H4 and all comparison language use those identities. | `ACCEPT` |
| A10-REV-004 | P2 | Station-level routing dispositions conflicted with regime-level applicability and allowed possible post-output station exclusion. | **Accepted.** Station technical eligibility and regime climate applicability are separate axes. Final routing is their conjunction. Post-output station climate exceptions are prohibited unless frozen prospectively. | `ACCEPT` |
| A10-REV-005 | P2 | Daymet's leap-year date discontinuity had no mandatory transform decision. | **Accepted.** M1 now freezes `calendar_transform_id`, February 29/absent December 31 behavior, civil-month ownership, masks, aggregations, sensitivities, and complete Gregorian generation. Silent relabeling or fabricated observations are prohibited. | `ACCEPT` |
| A10-REV-006 | P2 | M2 required authoritative A10 checkpoint/resume behavior before M4 implemented A10 model and data state. | **Accepted.** M2 now tests Slurm, storage, signals, and collectives with a synthetic harness. M4 performs the authoritative A10 model/optimizer/scheduler/scaler/RNG/sampler/data-cursor interruption-equivalence test. | `ACCEPT` |
| A10-REV-007 | P3 | B1's accepted A9 identity did not cover arbitrary A10-expanded stations or cells. | **Accepted.** Required B1 comparison is limited to inherited common A9 cells. Any expanded-panel renewal refit receives a new identity. Missing B1 evidence is unavailable, never favorable. | `ACCEPT` |
| A10-REV-008 | P3 | The confirmation manifest language conflated pre-access metadata with unread target-byte hashes. | **Accepted.** M7 seals a metadata/acquisition-request manifest. M8 records target content hashes only after controlled access. | `ACCEPT` |
| A10-REV-009 | P3 | Exact runtime boundaries lacked minimum-duration, contamination, and deterministic rerun rules. | **Accepted.** M3 now freezes repetition/minimum-duration logic, machine-quiescence acceptance, contamination rejection, dispersion reporting, and one deterministic rerun rule before candidate timing. | `ACCEPT` |
| A10-REV-010 | P3 | Warm initialization could hide generation work before timing. | **Accepted.** Pre-timer work is limited to model loading, immutable station conditioning, and initial-state construction. RNG advance, latent transition, requested-date inference, and requested-output materialization are prohibited. | `ACCEPT` |
| A10-REV-011 | P3 | The role table allowed development data for M5 screening while the M5 gate prohibited it. | **Accepted.** `fit_validation` owns M5 screening and ablations; `development` is reserved for M6 finalist comparison and applicability adjudication. | `ACCEPT` |
| A10-REV-012 | P3 | M6 allowed at most one qualifier even though the selector defined deterministic ordering among multiple survivors. | **Accepted.** M6 may retain multiple qualifiers, publishes all survivor evidence, and deterministically selects exactly one identity when the frozen ordering permits. | `ACCEPT` |
| A10-REV-013 | P3 | The confirmation-pass terminal requested another generic runtime study even though A10 already contains a normative runtime feasibility gate. | **Accepted.** The terminal now names a separately authorized production-implementation study. | `ACCEPT` |

## Executor-added finding

| ID | Severity | Finding | Disposition and correction | Recheck |
|---|---|---|---|---|
| A10-DISP-014 | P2 | M6 called a candidate sealed before M7 performed sealing, and M9 originally admitted only an M6 development hold or M8 decision. | **Accepted.** M6 now selects an identity, M7 seals it and emits the confirmation-ready terminal, and M9 accepts a hold reached at any prior milestone. The bounded recheck then audited every remaining selector/terminal reference. | `ACCEPT` |

## Post-disposition findings and dispositions

The first bounded recheck confirmed that A10-REV-001 through A10-REV-013 were
substantively resolved, then found three remaining terminal-flow inconsistencies.

| ID | Severity | Finding | Disposition and correction | Recheck |
|---|---|---|---|---|
| A10-POST-001 | P2 | Section 10.6 and H6 still said the selector sealed a candidate, and the firewall did not distinguish an M6 no-candidate hold from an M7 seal hold. | **Accepted.** The selector now chooses at most one identity for M7 sealing. The firewall separately names the M6 development hold and M7 confirmation-seal hold. | `ACCEPT` |
| A10-POST-002 | P2 | M8 had no operational hold for acquisition, identity, environment, or execution failure before a valid scientific score. | **Accepted.** `HOLD-A10-CONFIRMATION-EXECUTION` is now distinct from scientific confirmation failure and records exact target-access state without authorizing tuning or automatic retry. | `ACCEPT` |
| A10-POST-003 | P2 | M9 required a final performance benchmark even for an M0--M3 hold where no such evidence could exist. | **Accepted.** M9 verification and cleanup are conditional on the highest reached milestone. Later evidence is recorded as `not_reached`, never fabricated or treated as a passing/unavailable measurement. | `ACCEPT` |

The second bounded recheck found one final access-ledger edge.

| ID | Severity | Finding | Disposition and correction | Recheck |
|---|---|---|---|---|
| A10-FINAL-001 | P2 | A failure after entering `access_in_progress` but before parsing a value could leave the access state unresolved. | **Accepted.** Any target data byte read makes the state `consumed`. Rollback to `sealed` requires proof that no target byte was opened; uncertain access is conservatively `consumed`; no terminal may retain `access_in_progress`. | `ACCEPT` |

The final bounded recheck returned **ACCEPT** with no open P1 or P2 finding.

## Confirmed strengths

The independent reviewer confirmed that:

- the pivot and A9d interpretation are accurate, including the 18/4/2 funnel,
  three renewal degradations, 17 latent degradations, and no confirmation
  access;
- ADR-0002 is correctly applied and faithful mode remains comparator/fallback;
- neural-only and routed/fallback evidence remain separately reported;
- corpus roles, spatial tiling, missingness, source identities, and
  redistribution boundaries are strong;
- generation RNG is separated from training RNG and is batch/order independent;
- long-horizon, support, mixed-distribution, training-seed, and checkpoint
  requirements are thorough;
- official C3+3 and NVIDIA sources support the recorded L40, memory, volatile-
  partition, and offline-compute facts; and
- the then-reviewed single M0--M9 package structure avoided intermediate-
  package theater; the later operator amendment replaces it with one package
  per milestone while retaining the same anti-fragmentation rule inside each
  milestone.

## Verification record

Reviewer checks:

- review target commit identity confirmed;
- full 1,528-line initial plan read;
- `AGENTS.md`, ADR-0002, roadmap, A5b source assessment, A9a/A9c/A9d records,
  and the accepted CLI runtime benchmark checked;
- `python3 -m research.a9d.campaign verify-development` passed with 18 fits,
  24 staged evaluations, and 92 retained/19 report-only cells per horizon;
- all local Markdown links resolved;
- no duplicate headings or trailing whitespace; and
- `git diff --check` passed.

Final executor checks are recorded in the task handoff and must be rerun at
commit time. No Rust production function changed, so coverage/CRAP gates do not
apply to this planning-only disposition.

## Residual uncertainty

The review does not claim evidence that cannot exist before execution:

- live Lemhi driver, QOS/allocation, wall-time, preemption, requeue, scratch,
  and Apptainer behavior remain M2 measurements;
- corpus regime counts, multivariate co-observation coverage, volume, and storm
  support remain M1 measurements;
- the 800-GPU-hour ceiling and CPU runtime classification remain planning
  bounds until measured;
- acquired third-party terms and object identities remain M1 checks; and
- three training seeds remain a bounded feasibility design, not a universal
  uncertainty-sufficiency claim.
