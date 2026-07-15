# A9b consolidated calibration-harness review

Verdict: `ACCEPT`
Open P1 findings: 0
Open P2 findings: 0
Reviewed: 2026-07-15

## Scope and method

This review covers the research-tool implementation, exact A9a predecessor
binding, artifact/schema semantics, candidate and optimizer interfaces,
random-field/numerical vectors, recovery calibration, data-role leakage,
confirmation concurrency, append-only evidence, resource/storage behavior,
all FX-001--FX-020 results, command surfaces, requirement coverage, and
repository isolation. It does not review observed climate suitability because
A9b acquired no observed target and selected no candidate.

The review reproduced 14 predecessor hashes, 27 source/dependency records,
seven generated evidence identities, all five capitalized normative
requirements, and all eight commands. It ran 200 calibration plus 400
independent validation replications for each 100-year recovery class, replayed
the five core fixture artifacts byte-for-byte, validated the 31-objective
registry, executed package/unit/type/dependency checks, and ran the full Rust
repository gates. Six lenses were applied: accuracy and traceability,
statistical/numerical validity, model-class independence, role leakage and
one-shot access, deterministic/resource behavior, and public-interface
isolation.

## Findings and dispositions

No P1 or P2 finding remains open.

### A9B-REV-001 — latent recovery interval was overconservative (`P2`, resolved)

The first 200-member validation run gave 1.0 coverage for one latent-state wet-
probability interval, outside the prospectively allowed [0.90, 0.99] band.
The 95% calibration ensemble and quantile were not relaxed. The independent
validation ensemble was increased to 400, improving binomial resolution. All
scalar coverages now lie in [0.9075, 0.9875] for the latent class and [0.9025,
0.97] for renewal; joint coverages are 0.9575 and 0.9325 respectively. All four
predeclared fit seeds pass for each class.

### A9B-REV-002 — candidate received a bare fit ID (`P2`, resolved)

The first plugin interface accepted a fit ID string. That did not prove the
fit was valid or schema-matched. Plugins now accept only a `ValidatedFit`
created from a self-hash-verified `fit_valid` artifact whose candidate schema
hash matches the plugin. They receive no observed source rows, target metrics,
thresholds, ranks, strata, or competing output.

### A9B-REV-003 — access log and concurrent consumption were too weak (`P2`, resolved)

The first transition retained access events only inside the replaced manifest
and had no exclusive consumer lock. Access events now also form an immutable
hash chain written before state transition. An exclusive lock serializes the
sealed-to-consumed operation; lock contention, metadata-only consumption, and
second consumption all fail with stable reasons. FX-016 covers the lock plus
path, symlink, rename, copy, byte hash, logical hash, and normalized-key routes.

### A9B-REV-004 — objective and optimizer evidence was incomplete (`P2`, resolved)

The first green fixture run did not archive a 500-replicate null vector,
Pareto/selector reference, all attempt states, exact optimizer replay, or stale-
checkpoint recovery. The golden and resource artifacts now cover each. Null
replicates require identical family/horizon cells; unavailable and entirely
absent mandatory strata cannot pass.

### A9B-REV-005 — temporary path broke canonical replay (`P2`, resolved)

The first full replay correctly failed because FX-020 embedded its random host
temporary directory. Evidence now records the logical scratch filename and
content hash. A fresh full campaign reproduces all five core evidence files
byte-for-byte.

### A9B-REV-006 — fit/role semantic validation gaps (`P2`, resolved)

Fit-valid artifacts initially did not require nonempty passing monthly and
identifiability checks, and exposed evidence was compared to confirmation only
by logical hash. Valid fits now require parameters, support checks, moment
checks, and identifiability. Exposed/confirmation overlap is rejected by
normalized record key, object hash, or logical hash. The `fit` command now
produces the complete immutable A9 fit schema and checks every embedded source
against the role firewall.

## Conclusions by review lens

### Accuracy, numerics, and recovery

PASS. Canonical JSON rejects duplicates/nonfinite values and reproduces exact
bytes. Philox4x32-10 matches the Random123 zero vector; the A9 length-prefix,
SHA-derived key/counter, and component/domain vectors are frozen. Independent
and covariance-bearing monthly moments reconcile for 28/29/30/31 days;
omitting covariance fails. Simpson order 4096 integrates the reference vector
within `1e-10`. Both mock classes meet the frozen recovery coverage band.

### Model semantics and objective machinery

PASS. Renewal state is observable alternating spell type with no hidden
artifact. Latent state has interior wet probability and both emissions in all
three hidden states. Degenerate support returns `MODEL-CLASS-EQUIVALENCE`.
The complete 31-objective registry validates. Baseline-zero, availability,
500-replicate maximum-statistic, Pareto, and lexicographic references are
finite and exact. These mock results establish machinery, not climate merit.

### Leakage and confirmation access

PASS. All command inputs are strict and synthetic-only in A9b. Role overlap is
checked by path/alias/bytes/object/logical/normalized identity. Metadata reads
do not change state. Only `confirm` can lock, verify, log, and atomically
consume a complete synthetic seal. No network-client import, observed series,
or A9 confirmation target appears in the source/evidence manifests.

### Determinism, optimizer, and resources

PASS. Attempt and access records are immutable hash chains and reject unknown
entries or corruption. Complete, incomplete, hard-infeasible, and dominated
attempts remain durable. Proposal replay is byte-identical; one identical
infrastructure retry is allowed; stale and corrupt checkpoints fail; bounded
resume succeeds. Worker/memory/wall/evaluation/storage ceilings and the 10 MiB
LFS threshold are prospective and fail closed.

### Repository and promotion boundary

PASS. The harness lives entirely under `research/`; no file under `crates/` or
`reference/cligen532/` differs from dispatch. No station model, accepted
profile, runtime enum, candidate coefficient, observed fit, climate ranking,
or downstream integration was created. Coverage/CRAP is not triggered because
no production function changed.

## Residual uncertainty

- The two plugins and recovery fitters are synthetic mocks. Actual likelihood,
  identifiability, pooling, and observed-regime applicability belong to A9c.
- Exact f64 replay is frozen for the recorded Python 3.12 host/toolchain. A9c
  must either use that environment or prospectively qualify another before
  candidate output.
- Resource ceilings are interface-tested but not a benchmark of real A9c
  likelihood workloads. They may be reduced before candidate output, not
  enlarged in response to results.
- The confirmation roster remains metadata-only. No statement here concerns
  its target-data completeness or candidate performance.

These are downstream study obligations, not defects in the A9b harness.

## Verdict

A9b is `EXECUTED-COMPLETE` and returns `HARNESS-READY-A9C`. This authorizes no
A9c work, observed data access, climate claim, runtime pilot, or production
promotion without a separate operator dispatch.
