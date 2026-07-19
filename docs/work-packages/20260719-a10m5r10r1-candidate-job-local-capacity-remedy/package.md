# A10M5R10R1 — Candidate Job-Local Capacity Remedy

Status: `SCAFFOLDED`
Date: 2026-07-19
Evidence mode: Mixed
Starting branch and push target: current `main`, push `main`

## Objective

Execute a fresh, coherent rerun of the complete A10M5R10 architecture
portfolio without changing its scientific contract. The package remedies the
observed job-local exhaustion by limiting the campaign to two live candidate
jobs, admitting only one environment bootstrap at a time, deleting the
per-job wheelhouse and pip cache after verified installation, and preserving
bounded setup diagnostics outside supervised job-local storage.

## Predecessor evidence and frozen science

A10M5R10's control materialization passed, but its first eight candidate jobs
failed before Python science began. Four simultaneous jobs each expanded a
3.6 GB wheel archive and built a copied environment on the same 30 GB node
filesystem. The observed lower bound was 10,531,009,701 bytes per bootstrap;
the shared filesystem reached 98 percent use. Empty Slurm streams were not
diagnostic because setup logs lived under supervised job-local storage and
were removed by successful cleanup. These are operational failures and make
no statement about any candidate architecture.

This successor copies and authenticates the A10M5R10 portfolio contract and
all twelve direct and transitive science dependencies byte-for-byte under
`artifacts/science-dependency-identities.json`. Its authority builder also
requires operator-supplied paths and SHA-256 identities for R0's operational
summary, resource ledger, closed toolkit terminal receipt, and cleanup
receipt. It reruns the control and all ten
candidate-family/capacity roles under one new authority and run identity.
Results from the predecessor do not substitute for any successor role.

The package repeated the complete 1,440-object calendar/missingness scan. The
result in `artifacts/calendar-preflight.json` is byte-identical to R0 and binds
the revision-2 Daymet transform, normalized axis, observed masks, leap-year
fixtures, and core/physics counts before successor resource reservation.

## Frozen execution remedy

The control role completes first. Candidate roles then run in five ordered
waves of two:

1. monthly residual adapter K1 and K2;
2. annual/monthly residual adapter K1 and K2;
3. hierarchical joint-factor adapter K1 and K2;
4. climate-normal hierarchical state-space K1 and K2; and
5. physics-conditioned hierarchical adapter K1 and K2.

Within a wave, the first role is submitted alone. The second role may be
submitted only after the first publishes `setup.json` with successful pip
installation/check, deleted wheelhouse and pip cache, and
`ready_for_science: true`. The next wave may start only after both prior jobs
are terminal and observed and their evidence records show successful exact
job-local cleanup. At most two candidate jobs may be live, and at most one may
be bootstrapping.

These rules are executable admission conditions, not an operator checklist.
Before every toolkit submission, the current toolkit state and publication
receipts are copied into the owner-only staged run's `admission-input/`
directory. The standard-library `admission_checker.py` runs on the login host
against that staged snapshot, the staged operational contract and asset
manifest, and any required first-member `setup.json`. It atomically writes
the exact allowlisted `admissions/{role}.json` receipt only at that remote run
root. The toolkit submission follows immediately. Every job wrapper reads its
own receipt, and setup stops before runtime extraction unless the receipt's
self-hash, role, run, source commit, asset-manifest identity, decision, and
all admission gates authenticate. Thus a missing, local-only, stale,
wrong-role, or failed receipt cannot start science.

Each setup confines `TMPDIR`, `PIP_CACHE_DIR`, `XDG_CACHE_HOME`, and
`TORCH_HOME` to the supervised target. It publishes atomic, redacted,
64-KiB-bounded `setup.log` and structured `setup.json` records in the durable
role result directory. After `pip check`, the extracted wheelhouse and pip
cache are deleted and verified absent before the ready receipt is published
and before corpus extraction or science execution begins.

Every setup receipt is self-hashed and binds the run ID, role, Slurm job ID,
node, owner-marker hash, successor source commit, asset-manifest hash, and
submission-admission record. It independently authenticates the exact runtime
archive, wheelhouse archive, and requirements lock against the asset manifest.
The final control/candidate evidence reconstructs all of those checks instead
of trusting `setup.json`'s `valid` flag alone.

## Authority and resource bound

The operator authorized the corrective package and a complete portfolio
rerun. It permits one 30-minute one-L40 control predecessor, ten 90-minute
single-attempt one-L40 candidate roles, and one five-minute exact-node cleanup
reserve. The ceiling remains 935 GPU-minutes. There are no retries, arrays,
multi-rank jobs, candidate substitutions, or changes to the frozen objective,
calendar, data roles, model families, capacities, seeds, selector, or terminal
decision rules.

## Gates

- the predecessor portfolio contract and four science files match their
  frozen SHA-256 identities before and after asset materialization, together
  with all seven transitive science dependencies and the calendar profile;
- the full calendar preflight receipt has SHA-256
  `7f58a20eae635d9453ea86a473072b9e2597195ffc1d71660184d3e70b130a68`;
- authority creation binds operator-supplied hashes for the R0 operational
  summary, resource ledger, closed terminal, and verified cleanup records;
- the exact ten roles are partitioned into five ordered two-role waves;
- plan records allow only one attempt per role and preserve the 935
  GPU-minute ceiling;
- durable admission and setup evidence is allowlisted for the control and
  every candidate;
- all cache and temporary paths are contained by the supervised job-local
  target;
- wheelhouse and pip cache deletion is verified before science readiness;
- control precedes candidates, second-wave members obey setup admission, and
  later waves obey terminal-observed-cleanup admission;
- every role publishes scientific evidence, setup evidence, supervisor
  evidence, and successful cleanup before aggregation;
- the unchanged A10M5R10 selector replays over all ten successor results; and
- `git diff --check`, `cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test` pass.

Coverage/CRAP is not triggered because this package does not change production
functions under `crates/`.

## Exit criteria

Scientific terminals are exactly those frozen by A10M5R10:
`A10M5R10-PORTFOLIO-READY`, `HOLD-A10M5R10-SINGLE-CANDIDATE`,
`HOLD-A10M5R10-NO-CANDIDATE`, or an exact calendar, identity, role, support,
evidence, resource, or cleanup hold. An operational failure instead records an
exact `HOLD-A10M5R10R1-*` condition without interpreting candidate science.

## Artifacts

- `artifacts/job-local-capacity-contract.json` — operational freeze and wave
  admission policy;
- `artifacts/science-dependency-identities.json` and
  `artifacts/verify_science_identity.py` — direct/transitive science freeze;
- `artifacts/calendar-preflight.json` — complete successor calendar and
  missingness preflight receipt;
- `artifacts/admission-protocol.md` — exact staged-remote checker and immediate
  submission procedure;
- `artifacts/verify_freeze.py` — science identity and execution-policy
  verifier; and
- `artifacts/jobs/` — immutable asset preparation, authority/plan generation,
  remote admission enforcement, durable setup diagnostics, and complete
  control/candidate job sources.
