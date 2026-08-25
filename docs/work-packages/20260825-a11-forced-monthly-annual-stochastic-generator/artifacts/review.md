# A11 scaffold independent review

Date: 2026-08-25
Evidence mode: Static review of repository text; reviewer made no file changes
Reviewer: independent Codex subagent `a11_scaffold_review`

## Result

The reviewer reported no P0 findings, three P1 findings, two P2 findings, and
two P3 findings. All seven were accepted and corrected in the scaffold. No P1
or P2 finding remains open. This review does not substitute for the required
implementation/execution review at package terminal.

The same reviewer then performed a focused read-only closure review. It found
no remaining or newly introduced P0, P1, or P2 issue, verified the
zero-total/zero-wet-day edge, and independently reran the exact authored-text
and relative-link commands from `scaffold-gates.md`; both passed.

## Dispositions

### P1-1 — Repair prohibition contradicted conditional transforms

Disposition: **ACCEPTED / CORRECTED**.

The package and specification now prohibit output-time repair outside the
registered probability law while explicitly classifying the single wet-weight
normalization and temperature centering/scaling as structural conditional
sampling transforms.

### P1-2 — Temperature dispersion surfaces were conflated

Disposition: **ACCEPTED / CORRECTED**.

The forcing contract now separates interannual covariance of monthly mean
temperature, within-month daily mean-temperature residual SD, monthly mean
diurnal-range targets and interannual variance, and within-month daily
diurnal-range dispersion. Each must bind its own estimator, period, mask,
units, leap handling, and reconciliation or conditioning role.

### P1-3 — Independent PSD blocks did not prove joint feasibility

Disposition: **ACCEPTED / CORRECTED**.

Revision 1 must now freeze a joint block-dependence matrix or fully specified
conditional/copula construction spanning precipitation totals, wet counts,
monthly mean temperature, and diurnal range. Requested/effective cross-block
dependence, scale, feasibility, adjustment priority, and realized-scale
validation are mandatory.

### P2-1 — Transferable variation forcing versus target leakage was unclear

Disposition: **ACCEPTED / CORRECTED**.

The documents now distinguish candidate-fit-only estimator/product
construction from coordinate lookup in an already immutable transferable
product. The product identity, fixed period, coverage, estimator, and overlap
limitation must be frozen. Without such a product, the field is explicitly
region-pooled rather than derived from development or confirmation targets.

### P2-2 — Wet-count support was internally inconsistent

Disposition: **ACCEPTED / CORRECTED**.

Revision 1 now freezes a forcing-dependent feasible-count set for every
reachable starting state, and transition probabilities must give every emitted
count positive conditional support. Monthly amount/count support is joint:
`K = 0` if and only if the monthly total is zero; positive totals require
`1 <= K <= D`.

### P3-1 — Scaffold evidence was not fully reproducible

Disposition: **ACCEPTED / CORRECTED**.

`scaffold-gates.md` now records tool versions and exact commands for the local
relative-link validation and the changed-plus-untracked authored-text scan.

### P3-2 — ExecPlan deferred all executable commands

Disposition: **ACCEPTED / CORRECTED**.

The ExecPlan now contains exact commands and expected observations for current
repository inspection and gates. Revision-1 ratification remains responsible
for inserting exact paths and commands for scripts that do not yet exist,
before candidate output.

## Negative findings

The reviewer found no broken relative links, status/catalog mismatch,
accidental GPU or confirmation authority, missing aggregate-resource freeze,
or missing calendar/confirmation gate.

## Executed-package review — 2026-08-25

Reviewer: independent subagent `a11_scaffold_review` (read-only).

Disposition: **all findings accepted**. The preliminary scientific `FAIL` is
superseded. Attempt output is non-authoritative diagnostic material, the final
science status is `NOT_EVALUATED`, and the terminal is
`HOLD-A11-CONTRACT-NONCONFORMANCE`. No third attempt is authorized.

### P0 findings

1. The named base commit contains none of the attempted revision-1 freeze,
   implementation, or evaluator, and both attempts name it despite an
   implementation change. Both attempts are invalid as scientific evidence;
   retrospective publication/replay cannot repair prospective identity.
2. The executed generator has no annual transition, reports pre-PRISM regional
   covariance as the site-scaled reconciled surface, pools uncentered site
   climatologies as interannual variation, and changes 1,976 sampled wet-count
   targets through an unregistered rule. This is contract nonconformance, not
   evidence against the A11 thesis.
3. The attempt substituted a raw median for the frozen upper-90-percent paired
   bootstrap, lacked complete four-arm/WEPP evidence, and omitted registered
   daily/event, compound, runtime, storm, and context families. All
   climate-complete and climate-noninferiority claims are superseded.

### P1 findings

1. Stable ordinal ranks broke ties in the wet-fraction marginal and no
   requested/effective integer-count receipt exists.
2. The evidence schema leaves scientific nested records unconstrained;
   required source/resource/firewall/fixture/verifier artifacts are absent.
3. Calendar evidence is aggregate and does not prove the exact ordered axis,
   boundaries, per-object support, or PRISM cell/role mapping.
4. Metrics score f64 arrays while stream hashes identify an f32 cast; source
   and evaluator hashes are absent and attempt 0001's input hash has no backing
   artifact.
5. No confirmation access was found, but the claimed seal has no authenticated
   roster, custodian, metadata manifest, or firewall record.
6. Both authorized attempt slots are consumed; no third replay may be silently
   relabeled as verification.

### P2 findings

1. Evidence output bytes differ by six from the final file and there was no
   aggregate resource ledger.
2. Embedded and closeout terminals disagreed. The evidence audit now marks the
   embedded attempt claims invalid and establishes the sole closeout terminal.

The reviewer found no evidence of confirmation target leakage, GPU use,
production-profile mutation, or faithful-mode modification.
