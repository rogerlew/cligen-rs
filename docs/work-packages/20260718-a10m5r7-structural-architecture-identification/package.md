# A10M5R7 — Structural Architecture Identification

Status: `EXECUTED-HOLD-OBSERVATION-SHARD-PATH`
Date: 2026-07-18
Evidence mode: Mixed
Starting branch and push target: clean `main` at `7fa00e3`, push `main`

## Objective

Identify the smallest new A10 model architecture justified by the failed P1/P2
realized-temporal result. Attribute the accepted model's free-generation
failure, compare its accepted open-loop inference with observation-conditioned
and generated-feedback modes, and execute a fresh temporal adjudication only
if the prospectively frozen generated-feedback architecture passes the
diagnostic screen.

## Scope

Included:

- exact reconstruction of the three accepted P1 lognormal checkpoints;
- component-level signed residuals grouped into monthly climatology,
  occurrence/spells, precipitation distribution, temperature, and annual
  dependence;
- a seed-147031 comparison of accepted open-loop, observation-conditioned,
  and generated-feedback inference using the same weights;
- a deterministic decision tree that identifies exactly one next architecture
  hypothesis without changing the prior temporal gate;
- if eligible, 24 fresh 100-year generated-feedback streams per site across
  the three accepted seeds and the unchanged six-site temporal decision; and
- canonical Lemhi v2 execution, bounded accounting, collection, exact cleanup,
  repository gates, roadmap/catalog closure, and an explicit successor.

Excluded:

- changing the immutable A10M5R4 terminal or relabeling P1/P2;
- a new capacity ladder, amount-family screen, Transformer/diffusion search,
  N3/elevation acquisition, spatial comparison, public runtime, production
  Rust, development-selection access, or confirmation access;
- treating observation-conditioned output as a deployable generator; and
- changing the old temporal noninferiority thresholds after seeing results.

## Authority

- A10M5R3R1 supplies the exact P1 checkpoint identities and accepted family;
- A10M5R4R2R1R2 supplies the final empty temporal retained set and unchanged
  score;
- the A10 study plan supplies the intended state-space, persistence, memory,
  climate-conditioning, and coupled-output envelope; and
- `SPEC-A10-ARCHITECTURE-IDENTIFICATION` defines this new research-only
  diagnostic and generated-feedback surface.

The operator's 2026-07-18 dispatch authorizes this new scientific direction,
one package, current `origin/main`, and push to `main`. Protected roles remain
sealed.

## Plan

1. Freeze predecessor identities, inference modes, component groups, decision
   thresholds, seeds, sites, horizons, resource ceiling, and stop rules before
   reading component residuals or allocating.
2. Reconstruct P1 seed 147031 and run the three 30-year inference modes. Publish
   complete component residuals and replay the frozen decision tree.
3. If and only if generated feedback passes its frozen improvement and
   nondegradation guards, reconstruct the other two accepted P1 seeds and emit
   the registered 100-year generated-feedback matrix.
4. Reuse the exact accepted observations, faithful comparator, and stochastic-
   PRISM comparator to run the unchanged temporal noninferiority decision under
   a fresh candidate identity.
5. Close honestly at a temporal-ready result, an identified-but-unfitted next
   architecture, or a named mixed/operational hold; reconcile evidence,
   cleanup, roadmap/catalog, review, and repository gates.

## Resource ceiling

One primary one-L40 job of at most 60 minutes and one exact-node recovery job
of at most five minutes are authorized. The primary job is single-attempt. It
may reconstruct one checkpoint for diagnosis and, only after the in-job frozen
decision passes, reconstruct the other two P1 checkpoints. No retry, larger
capacity, additional family, or second primary job is authorized.

## Gates

- all accepted predecessor and corpus identities verify exactly;
- only `candidate_fit` contributes gradients and protected roles remain sealed;
- seed 147031 reproduces its accepted checkpoint payload and validation record;
- every inference mode publishes finite, supported, complete metrics;
- diagnostic grouping is attribution-only and the original temporal score is
  neither rewritten nor relaxed;
- the deterministic decision tree selects exactly one registered architecture
  hypothesis;
- full 100-year generation occurs only for a passing generated-feedback probe;
- any full candidate reproduces all three accepted checkpoint identities and
  has 24 streams per site;
- fresh temporal scoring uses the unchanged six sites, comparator identities,
  component scales, bootstrap seed, 1.25 median-upper limit, and 1.5 maximum
  limit;
- toolkit receipts, accounting, job-local and durable cleanup, and close
  reconcile; and
- Python/JSON parse, `git diff --check`, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test` pass.

Coverage/CRAP is not triggered because no production function under `crates/`
is changed.

## Exit criteria

- `A10M5R7-TEMPORAL-CANDIDATE-READY`: generated feedback passes the diagnostic
  and unchanged temporal gates;
- `A10M5R7-ARCHITECTURE-HYPOTHESIS-READY`: the diagnostic identifies one
  prospective architecture requiring a new fit contract;
- `HOLD-A10-ARCHITECTURE-HYPOTHESIS-MIXED`: no single registered mechanism
  explains enough of the residual;
- `HOLD-A10-GENERATED-FEEDBACK-SUPPORT`: generated feedback is non-finite or
  violates physical support; or
- the exact toolkit, environment, reconstruction, resource, or cleanup hold.

No terminal opens N3/elevation, spatial, development-selection, confirmation,
or production work automatically.

## Execution disposition

Run `a10m5r7-architecture-r0` settled at Slurm job `1014016` with exit 1
after 172 GPU-seconds (three ledger minutes). Seed 147031 reconstructed before
the probe failed while resolving the first observation shard. The loader used
`corpus/artifacts/daymet-008.tar.gz`; the hash-pinned corpus records the shard
under
`docs/work-packages/20260717-a10m1-corpus-role-freeze/raw/training/daymet-v2/`.
No diagnostic residual or generated-feedback output was published and no
protected role was opened.

The evidence allowlist was not satisfiable on this early failure, so toolkit
collection failed closed with `EVIDENCE_INCOMPLETE`. The authenticated gate,
Slurm streams, and supervisor record were preserved in restricted controller
state. The exact durable run root was then removed with the toolkit's
owner-marker-validated cleanup script and independently verified absent. R1
corrects only the shard path and failure-shaped evidence surface, preserves
the scientific freeze, and continues the original authority and budget.

## Artifacts

- `artifacts/design-freeze.md` and `diagnostic-contract.json` — prospective
  scientific and resource boundary;
- `artifacts/jobs/` — immutable probe and execution sources;
- `artifacts/residual-attribution.json` — signed component and grouped result;
- `artifacts/architecture-decision.json` — deterministic mechanism decision;
- `artifacts/temporal-decision.json` — conditional fresh temporal score;
- toolkit, accounting, cleanup, review, and gate records produced at execution.
