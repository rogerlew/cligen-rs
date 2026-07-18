# A10M5R3 — Candidate Family and Capacity/Runtime Knee

Status: `SCAFFOLDED`
Date: 2026-07-18
Evidence mode: Mixed
Starting branch and push target: `main` at the accepted A10M5R2 terminal,
push `main`

## Objective

Replace the dominated whole-wet-day GPD experiment with family-correct
positive-precipitation candidates, then locate a broad neural
architecture/runtime Pareto knee on the accepted A10M1 corpus and retain two
neighboring capacities for realized temporal and later spatial adjudication.

## Scope

Included:

- a revision-2 research model/configuration schema and executable validators;
- fixed-architecture N0 family comparison of lognormal, gamma, and a proper
  body-plus-threshold-GPD-excess formulation across three registered seeds;
- family-specific analytic and empirical tests for expectation, sampling,
  quantiles, support, and finite gradients;
- a five-point geometric capacity ladder on the accepted A10M1 corpus;
- clean-process CPU export/RSS, cold-load, nested 30/100-year runtime, GPU fit,
  export-size, support, stability, checkpoint, and stream-identity evidence;
- deterministic retention of the Pareto knee and its immediately larger
  passing frontier neighbor; and
- canonical Lemhi v2 toolkit lifecycle, bounded accounting, and exact cleanup.

Excluded:

- N3/elevation acquisition or any expanded target surface;
- development-selection or confirmation target bytes;
- spatial generalization claims, public generation profiles, production Rust,
  or a final architecture freeze;
- reuse or relabeling of A10M5 weights as successor evidence; and
- automatic addition of generalized gamma, mixtures, or temperature-family
  changes after results are seen.

## Authority

- [ADR-0005](../../decisions/0005-a10-refinement-before-spatial-promotion.md)
  and
  [SPEC-A10-REFINEMENT-TRAJECTORY](../../specifications/SPEC-A10-REFINEMENT-TRAJECTORY.md)
  govern the sequence.
- A10M1 v2 is the only corpus authority; A10M3 supplies the unchanged
  deterministic-generation, checkpoint, role, and absolute engineering
  contracts except where a prospectively published revision-2 configuration
  surface is required.
- A10M5 is immutable historical evidence. A10M5R1 supplies clean-process
  memory measurement. The accepted A10M5R2 terminal supplies the immediate
  operational anchor and is not edited by this package.
- Canonical Lemhi v2 and the accepted agent toolkit remain mandatory.

Accepted A10M5R2 operational anchors are the L64 lognormal depth-2 and depth-3
rows in both N0 and N1. Their fresh-worker `VmHWM` was 559--569 MB and their
external maximum RSS was 645--677 MB. R3 binds these as predecessor evidence;
it does not treat them as a family or final-capacity decision.

## Plan

1. Bind the accepted predecessor commits and publish the exact revision-2
   family/configuration schemas, seed schedule, configuration IDs, score
   ordering, parameter counts, resource ceiling, and stop rules before any
   allocation.
2. Implement family-specific likelihood, expectation, quantile, sampler,
   splice normalization, support, and empirical calibration tests; fail closed
   on any mismatch.
3. Run the nine-row fixed-N0 family screen on the accepted corpus and retain
   at most two family identities under the frozen ordering.
4. Run one seed at the five frozen capacity points for the winning family,
   compute the validation/runtime/resource Pareto frontier, and select two
   neighboring passing points without reading a protected role.
5. Run the two additional registered seeds for both retained capacities,
   adjudicate seed stability, and emit exactly two reconstructable capacity
   identities or an honest hold.
6. Reconcile raw evidence, requested/actual accounting, job-local and durable
   cleanup, toolkit close, repository gates, roadmap/catalog state, and the
   bounded A10M5R4 handoff.

## Resource ceiling

At most eighteen primary one-L40 jobs of 30 minutes each are authorized:
nine family rows, five one-seed capacity rows, and four additional-seed
frontier rows. One separate five-minute exact-node recovery allocation is
reserved. Jobs are single-attempt and sequential under the canonical toolkit;
no retry, family expansion, larger ladder, or time increase is authorized
without a prospective amendment committed and pushed before allocation.

## Gates

- the accepted 98-object A10M1 transfer manifest verifies exactly and no
  expanded N3/elevation object is staged or read;
- the old whole-wet-day GPD is unrepresentable in the successor schema;
- each family passes analytic and empirical expectation, quantile, sampling,
  support, finite-gradient, and deterministic-generation tests;
- all and only the prospectively frozen family and capacity rows execute under
  the registered seeds and resource limits;
- only `candidate_fit` affects fit state and `fit_validation` remains
  gradient-free; development-selection and confirmation access remain false;
- every retained configuration passes the unchanged 250 MiB export, 2 GiB
  clean RSS, 15-second cold-load, 30/100-year absolute runtime, 5x/10x
  classification, dispersion, support, stability, checkpoint, and stream-
  identity gates;
- the retained pair is the frozen Pareto knee and its immediately larger
  passing frontier neighbor; no final architecture or spatial claim is made;
- toolkit receipts, scheduler accounting, resource ledger, evidence hashes,
  exact job-local/durable cleanup, and close reconcile; and
- authored Python/shell/JSON parse and validate; `git diff --check`,
  `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, and
  `cargo test` pass. Coverage/CRAP is not triggered because production Rust is
  unchanged.

## Exit criteria

`A10M5R3-CAPACITY-PAIR-READY` requires one winning family and exactly two
reconstructable neighboring capacities that pass every hard gate. It
authorizes only A10M5R4 realized temporal-dispersion adjudication on the
accepted corpus.

Legitimate holds are `HOLD-A10-FAMILY-CALIBRATION`,
`HOLD-A10-NO-CAPACITY-PAIR`, `HOLD-A10-GENERATION-RUNTIME`,
`HOLD-A10-RESOURCE-BOUND`, or an exact toolkit/environment/cleanup terminal.
No hold opens the expanded spatial or confirmation roles.

## Artifacts

- `artifacts/design-freeze.md` — trajectory-derived prospective execution
  boundary, completed before allocation;
- revision-2 schemas, exact matrix, seed/resource contract, and executable
  verifier — created during design freeze;
- family/calibration, capacity/Pareto, fit/checkpoint, runtime/RSS, toolkit,
  accounting, cleanup, and terminal evidence — created during execution.
