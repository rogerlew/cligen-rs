# A10 Parallel Architecture Portfolio

This living ExecPlan follows `.agent/PLANS.md`. It coordinates A10M5R10
without replacing its package, specification, machine contract, evidence, or
terminal disposition.

## Purpose / Big Picture

A10M5R10 will replace the recent one-architecture-at-a-time cadence with one
prospectively frozen, parallel comparison. The observable outcome is a
complete matched-seed comparison of five candidate architecture families at
P1- and P2-scale capacity, followed by a deterministic Pareto decision that
retains up to three configurations. The campaign is ready to continue only if
at least two eligible configurations survive; otherwise it closes with an
honest scientific HOLD and complete comparison evidence.

The execution optimizes wall time rather than GPU-minute minimization. The
first run demonstrated that ten independent one-L40 roles are scientifically
appropriate but four simultaneous environment bootstraps are not operationally
admissible on the shared node-local filesystem. A10M5R10R1 therefore runs the
same ten roles in five two-job waves, admits only one authenticated bootstrap
at a time, and preserves three-seed evidence within each role without using
inefficient multi-rank synchronization.

## Progress

- [x] (2026-07-19) Audited A10M5R7 through A10M5R9 and the L40 operational
  qualification.
- [x] (2026-07-19) Froze five candidate families, two capacities, three seeds,
  common objective, physics boundary, eligibility, Pareto, and retention rule.
- [x] (2026-07-19) Scaffolded the package, research specification, machine
  contract, and this living ExecPlan.
- [x] (2026-07-19) Published immutable A10M5R10 implementation source and
  prospective verifier at `cbf73d781df09f466d66e31d2569ca19ffaa0faf`.
- [x] (2026-07-19) Passed complete core-plus-`srad` Daymet preflight before
  authority creation.
- [x] (2026-07-19) Initialized the first 935 GPU-minute authority and
  materialized all six controls exactly in job `1014028`.
- [x] (2026-07-19) Submitted and observed all ten first-run roles. Eight
  bootstraps failed from aggregate node-local capacity; physics jobs `1014039`
  and `1014040` passed, so the matrix remained incomplete.
- [x] (2026-07-19) Collected and closed the first run at
  `HOLD-A10M5R10-JOB-LOCAL-CAPACITY` with 103 charged GPU-minutes and exact
  cleanup.
- [x] (2026-07-19) Scaffolded A10M5R10R1 with unchanged science, complete byte
  pinning, authenticated setup/admission evidence, and five bounded waves.
- [x] (2026-07-19) Published A10M5R10R1 source at
  `6bde267235c9a3cddababe981cba5986e4fd8ca2`, replayed the exact preflight,
  and initialized its fresh authority.
- [x] (2026-07-19) Closed A10M5R10R1 at
  `HOLD-A10M5R10R1-PYTHON311-CONTROL-PLANE`: control job `1014042` failed
  before setup under the host Python 3.6, no science opened, all eleven
  job-local cleanups passed, and the exact remote root was removed.
- [x] (2026-07-19) Hardened the general toolkit under A10M5O1R2 with an atomic
  upstream-failure matrix stop and authenticated sparse collection; independent
  review and all 79 toolkit tests passed.
- [x] (2026-07-19) Scaffolded A10M5R10R1R1 with unchanged byte-pinned science,
  explicit `/usr/bin/python3.11` login/compute control-plane execution, exact
  R1/toolkit-hardening predecessor bindings, and a real authority-initialization
  smoke test.
- [x] (2026-07-19) Published A10M5R10R1R1 at `9bdee723…`, replayed the full
  calendar, staged and verified assets, and admitted control job `1014053`.
- [x] (2026-07-19) Closed A10M5R10R1R1 at
  `HOLD-A10M5R10R1R1-COMPUTE-PYTHON311-ABSENT`: node03 lacked the login-only
  interpreter, no science opened, no candidate was submitted, and exact
  job-local/durable cleanup passed.
- [x] (2026-07-19) Scaffolded and independently reviewed A10M5R10R1R2 with
  POSIX portable-runtime extraction, a 65,536-byte pre-runtime log cap,
  Python-3.6-compatible failed-gate publication, and unchanged science.
- [x] (2026-07-19) Published A10M5R10R1R2 at `c63ab18…`, replayed preflight,
  initialized authority `f08dd107…`, and proved the portable setup path in job
  `1014054` before control materialization exposed a corpus-root nesting defect.
- [x] (2026-07-19) Observed the authenticated failed control, stopped all ten
  never-submitted roles, collected sparse evidence, released recovery, and
  closed at `HOLD-A10M5R10R1R2-CORPUS-ROOT-NESTING` after two GPU-minutes.
- [x] (2026-07-19) Scaffolded and independently reviewed A10M5R10R1R3 with
  only the two parent-root extraction corrections, a self-authenticated corpus
  layout pin, and coordinated pin/archive/manifest drift rejection.
- [x] (2026-07-19) Published A10M5R10R1R3 at `7cc30f8…`; job `1014056`
  proved corpus extraction and calendar preflight, then exposed a child-only
  CuBLAS environment export at the first batch's output head before loss.
- [x] (2026-07-19) Closed A10M5R10R1R3 at
  `HOLD-A10M5R10R1R3-CUBLAS-ENVIRONMENT-SCOPE` after five GPU-minutes with
  authenticated matrix stop, sparse collection, cleanup, and reserve release.
- [x] (2026-07-19) Scaffolded and independently accepted A10M5R10R1R4 with
  exact seven-variable parent science-environment reconstruction in both
  wrappers, hostile inherited-variable clearing, and mutation guards.
- [ ] Publish and execute the fresh A10M5R10R1R4 science-environment remedy,
  then dispatch, authenticate, observe, and collect its ten candidate roles
  under machine-enforced wave admission.
- [ ] Aggregate all thirty candidate seed rows, replay eligibility/Pareto
  retention, and publish the terminal.
- [ ] Reconcile accounting, exact cleanup, reserve, authority close, package
  records, review, and repository gates.

## Surprises & Discoveries

- A10M5R7's residual was mixed rather than dominated by one mechanism. Raw
  generated feedback worsened family-balanced error by 17.26%, so the
  portfolio excludes daily generated-feedback architectures.
- A10M5R8 improved its climate score 14.35% but more than doubled daily proper
  NLL and degraded location. Objective pressure alone is insufficient.
- A10M5R9's 30-parameter monthly residual improved its matched dispersion
  composite 15.15% without degrading its baseline blocks. Its failure against
  P1 came from the smaller replacement baseline, which motivates both frozen-
  backbone adapters and a capacity-matched replacement arm.
- A10M5R8 and R9 selected checkpoints at their epoch ceilings. The portfolio
  therefore freezes a longer 96-epoch maximum rather than interpreting either
  earlier ceiling as convergence.
- Four-rank NCCL on node03 uses host shared memory and is markedly slower than
  one GPU. Ten independent one-GPU jobs provide useful concurrency without
  that communication path.
- Four simultaneous A10M5R10 environment bootstraps each needed at least
  10.53 GB before science. Two successive four-job batches exhausted the
  shared temporary filesystem; two concurrent jobs then completed normally.
  Per-job capacity checks did not account for aggregate same-node expansion.
- Setup diagnostics originally lived only under supervised job-local roots,
  so successful cleanup erased the failure detail and left empty Slurm
  streams. Durable redacted setup and admission receipts are required before
  the corrective authority opens.
- Lemhi's compute-node `/usr/bin/python3` is Python 3.6 even though
  `/usr/bin/python3.11` is installed and used successfully by the login-side
  admission checker. Pre-runtime diagnostics cannot rely on the default
  interpreter before the portable science runtime is extracted.
- Lemhi's compute image also lacks `/usr/bin/python3.11` entirely. An absolute
  interpreter path proven on the login host is not a compute capability proof;
  portable-runtime extraction must precede Python 3.11 diagnostics.
- The portable bootstrap passed on node03, exposing a latent R1 wrapper change:
  the archive already has a `corpus/` root, so extracting it into
  `$job_local/corpus` created `$job_local/corpus/corpus`. R0 had correctly
  extracted into `$job_local`; the two later pre-runtime failures masked this
  separate science-entry defect.
- After the corpus correction passed, deterministic training exposed a second
  R1 refactor scope error: `CUBLAS_WORKSPACE_CONFIG` was exported in the child
  bootstrap but not the `--export=NONE` parent launcher, so it could not reach
  the output-head linear call where deterministic PyTorch rejected its
  absence.
- A PASS-only admission surface made the old evidence allowlist impossible to
  collect after an upstream pre-admission failure. The toolkit now separates
  maximum allowlisting from exact presence while retaining mandatory evidence
  for every submitted attempt and invoked recovery.

## Decision Log

- Compare a portfolio now because operator time and serial scientific latency,
  not GPU minutes, are the active constraint.
- Use exact P1/P2 and their three accepted seeds so capacity and seed effects
  remain connected to reconstructable controls.
- Keep monthly and annual dispersion in the training signal and make all seven
  core climate blocks equal. Daily target pairing remains zero because the
  claim concerns stochastic climate, not reproduction of observed daily
  sequences.
- Include monthly-only, annual/monthly, shared-factor, climate-normal, and
  physics-conditioned families. This tests increasing structure through
  explicit paired differences without an unbounded model search.
- Treat observed Daymet `srad` only as a target. Latitude and day of year create
  a deterministic astronomical envelope; shared generated factors represent
  precipitation/radiation/temperature dependence without observed-weather
  input or target leakage.
- Run all three seeds within each family-capacity role. A failed role cannot be
  silently completed by another job or retried after outcome inspection.
- Retain multiple eligible Pareto configurations rather than forcing a single
  winner. Two retained configurations are required for a READY terminal.
- Do not splice the two successful first-run physics roles into a later
  portfolio. A coherent selector lineage requires a fresh control and all ten
  candidate roles under one corrective run identity.
- Preserve useful concurrency with five waves of two live jobs. Submit the
  second member only after the first proves setup complete and payload cleanup;
  admit the next wave only after both prior roles are terminal, observed, and
  job-local-clean.
- Preserve A10M5R10R1 as an operational HOLD. Use a fresh run identity for the
  Python 3.11 remedy, and use the toolkit's atomic whole-matrix stop if a future
  exhausted upstream role makes unsubmitted dependents scientifically moot.
- Preserve A10M5R10R1R1 as a second operational HOLD. Do not probe additional
  host Python paths. Use POSIX extraction of the already verified portable
  runtime and ensure a Python-3.6-compatible minimal false gate exists for
  failures before that runtime is usable.
- Preserve A10M5R10R1R2 as a third operational HOLD. Restore the exact R0
  parent-directory corpus extraction in both control and candidate wrappers;
  do not repack the archive or use a new strip-components interpretation.
- Preserve A10M5R10R1R3 as a fourth operational HOLD. Restore the frozen
  science environment explicitly in both parent launchers; do not weaken
  PyTorch deterministic-algorithm enforcement.

## Outcomes & Retrospective

The first package run consumed 103 charged GPU-minutes and closed cleanly at an
operational HOLD. Its exact controls and two physics results demonstrate that
the corrected science code runs, but eight missing candidate roles prohibit
selection or architecture interpretation. A10M5R10R1 then consumed 11 charged
GPU-minutes and failed before any science because its control-plane interpreter
was not qualified. Its admission firewall and cleanup worked, but its evidence
surface also exposed the general terminal-closure gap now closed by A10M5O1R2.
The A10M5R10R1R1 run then spent one GPU-minute proving that compute node03 has
no `/usr/bin/python3.11`; no science opened and no candidate was submitted. Its
job-local cleanup passed, but the missing interpreter also prevented gate
publication and therefore normal toolkit closure. The active scientific
successor is A10M5R10R1R2 with unchanged science, POSIX portable-runtime
bootstrap, a host-compatible minimal failure gate, and the hardened toolkit.
R1R2 proved that bootstrap but then spent two GPU-minutes exposing a latent
corpus-root nesting defect before any control was materialized. Its failed gate,
whole-matrix stop, sparse collection, cleanup, reserve release, and closure all
passed. R1R3 corrected that root and reached the first P1 control training
batch output head, where it spent five GPU-minutes exposing a child-only CuBLAS
environment export. Its terminal closure also passed. The active successor is
A10M5R10R1R4, restoring the frozen science environment in both parent launchers
without weakening deterministic execution. This section
must be updated after that execution with all ten family/capacity
results, retained identities, resource use, operational reconciliation, and
the realized wall-time effect of bounded concurrency.

## Context and Orientation

The authoritative package is
`docs/work-packages/20260719-a10m5r10-parallel-architecture-portfolio/package.md`.
The research interface is
`docs/specifications/SPEC-A10-ARCHITECTURE-PORTFOLIO.md`, and its exact machine
freeze is `artifacts/portfolio-contract.json` below the package. Execution
sources will live in the package's `artifacts/jobs/` directory. Prospective and
result verifiers will be `artifacts/verify_freeze.py` and
`artifacts/verify_result.py`.

P1/P2 accepted identities are recorded in
`docs/work-packages/20260718-a10m5r4r2-realized-temporal-adjudication/artifacts/temporal-contract.json`.
The common climate score is defined by
`docs/specifications/SPEC-A10-CLIMATE-STATISTICS-TRAINING.md`. Calendar and
missingness behavior comes from `docs/specifications/SPEC-A10-CORPUS.md` and
`docs/specifications/a10-daymet-calendar-profile-v1.json`.

In this plan, a family-capacity role is one Slurm job that runs all three seeds
for one architecture at K1 or K2. A matched-control ratio divides a candidate's
error by the exact same-capacity, same-seed control error; lower is better. A
Pareto configuration is one for which no eligible peer is effectively no worse
on every registered decision axis and at least 2% better on one.

## Plan of Work

### Milestone 1: prospective implementation and preflight

Implement the shared architecture, objective, scoring, selector, and dispatch
code under the package's `artifacts/jobs/`. Add a prospective verifier that
constructs every architecture/capacity, checks state centering and output
support, proves role enumeration and decision fixtures, and rejects observed
weather inputs. Run a complete standard-library calendar preflight over all
1,440 candidate-fit and fit-validation Daymet objects, including the extra
`srad` mask. Acceptance is a hash-bound receipt showing the exact revision-2
counts before any authority or ledger exists.

### Milestone 2: controls and parallel portfolio

Publish and push the exact source commit, prepare immutable assets, and
initialize one authority with a 935 GPU-minute ceiling. The 30-minute
predecessor reconstructs P1 and P2 for all three seeds and publishes immutable
control/checkpoint/random-field records. Acceptance is six exact checkpoint
identities and no protected-role access.

The first run submitted the ten family-capacity roles after the predecessor
succeeded and exposed an aggregate bootstrap-capacity defect. The corrective
run submits five deterministic waves of two. The second role in a wave waits
for an authenticated setup-ready receipt from the first; the next wave waits
for both roles to be terminal, toolkit-observed, and job-local-clean. Each role
still requests one typed L40 for 90 minutes, verifies its assets and calendar
locally, executes its three seeds, scores all 240 validation points, publishes
complete learning curves and metrics, and removes job-local state. Acceptance
is ten authenticated terminal receipts and thirty complete candidate rows;
partial rows remain failures rather than being imputed.

### Milestone 3: decision and closure

Collect all sanitized evidence and run the CPU aggregator over the immutable
rows. It computes matched-control ratios, three-seed summaries, eligibility,
Pareto dominance, deterministic retention, and the typed terminal. Acceptance
is an independently replayable decision retaining zero through three exact
configuration identities.

Perform owner-marker-validated cleanup for every exact durable and remote root,
using the five-minute reserve only if ordinary cleanup cannot be authenticated.
Close the authority and reconcile requested versus actual resources. Update
the package, this plan, catalog/roadmap as separately authorized, disposition,
review, gate results, and hashes. Acceptance is closed accounting, absent exact
roots, passing result verifier, and passing repository gates.

## Concrete Steps

Run from `/Users/roger/src/cligen-rs`. Before authority creation:

    python3 docs/work-packages/20260719-a10m5r10-parallel-architecture-portfolio/artifacts/verify_freeze.py
    python3 docs/work-packages/20260719-a10m5r10-parallel-architecture-portfolio/artifacts/verify_corpus_calendar.py --corpus-tar <private-corpus.tar>

The executor must record the exact source commit and use package-scoped private
controller and ledger roots. Prepare and verify assets using
`research/a10/lemhi_toolkit`, then execute the registered
`control-materialization` role. Only an authenticated passing predecessor may
release all ten one-L40 role submissions. Submit them without DDP/NCCL and
observe each role exactly once. Concrete toolkit commands, run IDs, authority
hashes, Slurm job IDs, and collection commands must be appended here when the
implementation fixes those identifiers.

For A10M5R10R1R2, set `RUN_ID` to
`a10m5r10r1r2-portable-bootstrap-control-plane-remedy-r0`, set `LOCAL_RUN_STATE` to
the package-private toolkit run state, and set `REMOTE_RUN_ROOT` to the exact
staged run root. Every submission uses this admission sequence:

1. Copy the current toolkit `private/state.json` to
   `REMOTE_RUN_ROOT/admission-input/state.json`. Copy all currently published
   `job-*.json` receipts needed by the target gate into
   `REMOTE_RUN_ROOT/admission-input/publication/`. Do not copy or edit toolkit
   state in the other direction.
2. On the login host, run staged `admission_checker.py` explicitly with
   `/usr/bin/python3.11` and the staged
   `job-local-capacity-contract.json`, `asset-manifest.json`, copied state,
   copied publication directory, exact remote root, target role, and exact
   `admissions/{role}.json` output. For the second role in a wave, also pass
   `--setup first-role=REMOTE_RUN_ROOT/results/first-role/setup.json`.
3. Require exit zero and authenticate the receipt's `PASS`, role, run, plan,
   source, asset-manifest, input hashes, and all-true gates. Immediately invoke
   the toolkit's serial `submit --job-role ROLE --attempt-index 0`. The remote
   job wrapper independently rejects a missing, stale, wrong-role, or failed
   receipt before runtime extraction.
4. After the first role is submitted, poll only its durable `setup.json` until
   the self-hash, scheduler identity, admission identity, exact staged assets,
   pip install/check, payload deletion, and `ready_for_science` all pass. Then
   refresh the state snapshot, admit, and submit the second role.
5. Wait for both roles to become scheduler-terminal. Inspect their final
   evidence and accounting, then invoke toolkit `observe` exactly once per
   role, serially. Refresh the state and publication snapshots only after both
   observations. The next wave's first-role admission must prove both prior
   job receipts terminal and `job_local_cleanup: true`.

The five exact waves are monthly K1/K2, annual-monthly K1/K2, joint-factor
K1/K2, climate-normal K1/K2, and physics-conditioned K1/K2. At no point may a
third candidate be live or a second environment be bootstrapping. A failed
admission receipt is evidence, not permission to bypass the checker. Any
ambiguous job-local cleanup follows the toolkit's one exact-node recovery path;
the five-minute reserve never runs science.

After collection, run the package result verifier and repository gates:

    python3 docs/work-packages/20260719-a10m5r10-parallel-architecture-portfolio/artifacts/verify_result.py
    git diff --check
    cargo fmt --check
    cargo clippy --all-targets -- -D warnings
    cargo test

If production functions under `crates/` are changed, additionally run the
workspace coverage and CRAP gates required by `AGENTS.md`.

## Validation and Acceptance

Prospective acceptance requires exact agreement between package, specification,
contract, implementation role table, seeds, capacity shapes, objective weights,
members, epochs, calendar counts, resource ceiling, and terminal fixtures. The
preflight must demonstrate 10,958/10,950 full-period core and physics counts,
2,922/2,920 representative-window counts, observed February 29, absent
leap-year December 31, exclusive target-end behavior, at least 28 observations
per year-month, and all 1,440 role-eligible objects.

The A10M5R10R1R2 source commit must contain the successor package, be pushed to
`main`, descend from toolkit-hardening commit
`0ddffd9ac5db2440f74f54285e0df1c2ac856c98`, and have no diff from that commit
over the four protected toolkit implementation paths. Before authority
creation, the executor must replay the full 1,440-object scan from the retained
corpus and require byte equality with the frozen preflight receipt.

Execution acceptance requires six exact controls; ten single-attempt
family-capacity roles; thirty complete candidate rows; candidate-fit-only
normalization and gradients; gradient-free fit-validation; sealed protected
roles; finite supported sixteen-member generation; all-240 scores; parameter,
epoch, and resource compliance; and deterministic selector replay.

Operational acceptance requires authenticated terminal accounting at or below
935 GPU-minutes, sanitized evidence collection, job-local and durable exact
cleanup, reserve settlement, authority close, and repository gates. Scientific
READY is separate: at least two eligible Pareto configurations must be
retained.

## Idempotence and Recovery

Prospective verifiers, the calendar scan, aggregation, result verification,
and repository gates are repeatable and read-only with respect to frozen
evidence. Asset preparation may be repeated only before authority creation and
must reproduce hashes.

Once an authority exists, never reset, copy, or replace its ledger. A role is
single-attempt; after ambiguous scheduler state, authenticate terminal state
and use only the toolkit's exact role/run recovery path. The five-minute
reserve authorizes cleanup, not training or a scientific retry. Do not resubmit
a failed role under another ID, combine partial seeds, or change thresholds.
If cleanup cannot be proved after the one bounded recovery, preserve evidence
and close with an exact cleanup hold.

## Artifacts and Notes

- `artifacts/portfolio-contract.json` is the prospective machine freeze.
- `artifacts/calendar-preflight.json` will bind full corpus mask evidence.
- `artifacts/control-materialization.json` will bind all six controls.
- `artifacts/portfolio-summary.json` will contain all seed and aggregate rows.
- `artifacts/portfolio-decision.json` will contain eligibility, Pareto, and
  retained identities.
- `artifacts/execution-disposition.md` will explain the scientific terminal.
- `artifacts/resource-ledger.md` and `toolkit-records.md` will reconcile live
  operations without publishing private paths or credentials.
- `artifacts/review.md`, `gate-results.md`, and `verify_result.py` will close
  the evidence and repository state.

## Interfaces and Dependencies

The experiment depends on Python 3.11, NumPy, PyTorch, the private immutable A10
corpus, accepted P1/P2 reconstruction sources, the Daymet revision-2 calendar
profile, Slurm, one typed L40 per role, and
`research/a10/lemhi_toolkit`. The physics arm requires the existing Daymet
`srad` field but no external acquisition. The package changes no Rust runtime,
faithful generator, public CLI, or production model interface.

The downstream research interface is a list of zero through three exact
retained architecture/capacity identities and their complete comparison
evidence. Any later temporal, spatial, confirmation, public-profile, or
production work requires separate authority.

## Revision note

2026-07-19: created the prospective parallel portfolio plan with five families,
two matched capacities, three seeds, ten independent one-L40 roles, and a
frozen multi-candidate Pareto decision.

2026-07-19: recorded the first run's aggregate job-local capacity HOLD and
continued under A10M5R10R1 with complete science byte pinning, durable setup
diagnostics, authenticated submission admission, and five two-role waves.

2026-07-19: recorded A10M5R10R1's pre-runtime Python 3.6 HOLD and exact manual
cleanup, completed A10M5O1R2 terminal-failure closure hardening, and continued
the unchanged science toward a fresh Python 3.11 control-plane remedy.

2026-07-19: recorded A10M5R10R1R1's compute-node Python 3.11 absence and exact
cleanup, then continued the unchanged science toward a portable-runtime-first
control plane with an observable pre-runtime failure path.

2026-07-19: scaffolded the A10M5R10R1R2 portable-bootstrap successor and
accepted it after independent review. The review required admission to close
after an observed failed role and capped the POSIX pre-runtime setup log at
65,536 bytes before execution authority could open.

2026-07-19: closed A10M5R10R1R2 after it proved portable bootstrap but exposed
the inherited nested corpus extraction root. The hardened matrix stop and
sparse evidence closure passed; the bounded R1R3 successor restores only the
two R0 extraction destinations.

2026-07-19: scaffolded A10M5R10R1R3 and accepted it after independent review.
The review required the corpus-layout pin itself to be byte/SHA authenticated
before authority creation and proved coordinated pin/archive/manifest drift is
rejected.

2026-07-19: closed A10M5R10R1R3 after its extraction fix passed and the first
control training operation exposed child-only CuBLAS environment scope. The
bounded R1R4 successor restores deterministic science environment closure in
both parent wrappers.

2026-07-19: scaffolded A10M5R10R1R4 and accepted it after independent review.
The package reconstructs and asserts the complete frozen seven-variable
science environment in both parent launchers before any parent Python process;
science, corpus, calendar, roles, waves, and the 935-minute ceiling are
unchanged.
