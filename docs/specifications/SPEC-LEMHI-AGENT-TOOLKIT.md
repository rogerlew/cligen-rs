# SPEC-LEMHI-AGENT-TOOLKIT — Lemhi Agent Workflow Toolkit

Status: authoritative revision 2; hardening extended 2026-07-19
Owning packages:
[foundation](../work-packages/20260717-a10-lemhi-toolkit-foundation/package.md)
and
[A10M4O1 hardening](../work-packages/20260717-a10m4o1-lemhi-operational-hardening/package.md),
[A10M5O1R1 evidence projection](../work-packages/20260719-a10m5o1r1-evidence-token-projection-hardening/package.md),
and
[A10M5O1R2 terminal failure closure](../work-packages/20260719-a10m5o1r2-terminal-failure-closure-hardening/package.md)

## 1. Surface

This specification defines the repository-local toolkit used by authorized
agents to prepare, validate, stage, submit, observe, collect, and clean bounded
Lemhi work from `rmm`. It specifies command semantics, state transitions,
records, provider boundaries, safety invariants, and failure behavior.

The toolkit is operational research infrastructure. It is not a CLIGEN
runtime interface, generation profile, environment manager, credential agent,
Slurm replacement, or cluster configuration authority.

Normative terms `MUST`, `MUST NOT`, `SHOULD`, and `MAY` are interpreted as in
RFC 2119. Examples are nonnormative unless explicitly labeled otherwise.

## 2. Producers, consumers, and authority

The toolkit and its committed provider definitions produce private operational
state, plans, scripts, and sanitized publication receipts. Agents and work
packages consume them. OpenSSH, Slurm, the selected runtime/provider artifacts,
and the live Lemhi nodes produce external observations consumed by the toolkit.

Authority order is:

1. the dispatched work package's scientific scope, resource ceiling, stop
   rules, confirmation classification, and exact cleanup authority;
2. this specification for toolkit behavior;
3. the agent compute guide and accepted A10 operational evidence;
4. timestamped live observations for current cluster capability; and
5. public documentation and cached receipts as hypotheses only.

The toolkit MUST refuse a request whose package authority is absent,
ambiguous, internally inconsistent, or exceeded. It MUST NOT broaden a
scientific claim merely because a lower-level operational check passes.

Every dispatch has one immutable `authority_id`. Every resource ceiling has a
`resource_budget_id` bound to that authority. All runs, plan revisions,
attempts, retries, and recovery actions under the dispatch share that identity
and budget; creating a new `run_id` or `plan_id` never resets authority or
accounting.

## 3. Design principles

1. **Thin orchestration.** Reuse OpenSSH, Slurm, `tar`, hash tools, and an
   explicitly selected environment provider. Do not reimplement them.
2. **Bootstrap independence.** The `rmm` controller MUST NOT require Lemhi's
   Python. Remote bootstrap/staging operations MUST work with POSIX `sh` plus
   commands declared by the cluster profile. Job and provider runners MAY use
   another profile-declared, probed interpreter such as `/bin/bash`.
3. **Discovery is not proof.** A visible module, file, wheel, GPU, or cached
   receipt is only a candidate until the relevant compute-side gate passes.
4. **Frozen plan revisions.** Selection and resource decisions are immutable
   for started work. A prospective amendment creates a new revision with
   explicit lineage and may affect only unstarted work.
5. **Exact ownership.** Every remote and job-local object created by the
   toolkit belongs to one registered run. Cleanup never infers targets.
6. **Replaceable providers.** Dependency evolution occurs through versioned
   provider contracts and explicit policy, never silent fallback.
7. **Evidence before claims.** Terminal classification uses explicit gate
   results plus scheduler receipts, not process exit alone.
8. **Separated operational and publication state.** Retain exact private state
   long enough to operate safely, but publish only a sanitized projection that
   excludes credentials, usernames, home paths, control socket paths, GPU
   UUIDs, and unrestricted environment dumps.

## 4. Trust and execution boundary

The control plane runs on `rmm`. It MAY use a repository-local implementation
language selected by the owning package, but the minimum deployment MUST have
no third-party runtime dependency beyond tools already validated on `rmm`.

The remote bootstrap/staging runner is committed POSIX `sh`. Each job or
provider runner MUST declare and probe its exact interpreter in the
content-hashed cluster profile. A provider MAY introduce a runtime only after
its archive and platform contract are verified. No earlier toolkit phase may
depend on that runtime.

Cold authentication is human-only. The toolkit:

- MUST resolve logical `gateway` and `target` endpoints from the content-hashed
  cluster profile; revision 1 defaults are `login-ui` and `lemhi`;
- MUST check both existing masters immediately before every remote operation
  and after a long transfer before submission or cleanup;
- MUST use `BatchMode=yes`, a finite connection timeout, and a finite total
  subprocess timeout on the actual operation;
- MUST prohibit automatic creation of a cold master by toolkit operations;
- MUST fail with `AUTH_BOOTSTRAP_REQUIRED` if either master is unavailable;
- MUST NOT initiate password, keyboard-interactive, Duo, host-key acceptance,
  or credential-storage workflows; and
- MUST NOT weaken host-key or transport verification.

Read-only local planning may proceed without SSH. No cached result may be
presented as a live observation.

## 5. Lifecycle and state machine

The normative run lifecycle is:

```text
AUTHORITY_CHECKED
  -> DISCOVERED
  -> PLANNED
  -> PREPARED
  -> STAGED
  -> VERIFIED
  -> MATRIX_ACTIVE
  -> MATRIX_SETTLED
  -> COLLECTED
  -> CLEANED
  -> CLOSED
```

Each `(job_role, attempt_index)` has a separate repeatable attempt lifecycle:

```text
REGISTERED -> RESERVED -> SUBMITTED -> TERMINAL_OBSERVED -> RESULT_VALIDATED
```

Parallel attempts are independent state objects. A retry is a new prospective
attempt index. `MATRIX_ACTIVE` begins with the first registered attempt and
reaches `MATRIX_SETTLED` only when the complete matrix and stop ladder are
settled. Transfer-only packages omit both matrix states. `CLEANED` is optional
only when the frozen plan creates no ephemeral remote or job-local state.
`DISCOVERED` contains nonallocating control/login observations only. Compute
observation requires an already frozen plan and registered bounded attempt;
`probe` MUST NOT create unplanned Slurm work.

Every state-changing transition MUST hold a single-writer per-run lock and
emit a transition event. Resource reservation and ledger transitions MUST
also hold the single-writer lock for `resource_budget_id`, across all runs.
When both locks are needed, the authority-budget lock is always acquired
before the run lock and released after it; implementations MUST NOT reverse
this order.
Before a plan exists, events bind authority, configuration, and capability
hashes. After planning, events additionally bind `plan_id`. Attempt events
also bind job role and attempt index. A failed transition retains the last
valid state and a typed error; it MUST NOT manufacture the next event.

The user-facing command vocabulary is normative even if implementation groups
commands differently:

| Command | Transition / responsibility |
|---|---|
| `doctor` | local tools, repository state, SSH master, and authority preflight |
| `probe` | timestamped, nonallocating control or login discovery |
| `plan` | deterministic provider, asset, resource, gate, and cleanup selection |
| `prepare` | resolve and hash local immutable assets without remote mutation |
| `stage` | transfer into the registered run using partial-name promotion |
| `verify` | verify staged identities and compute-side preconditions |
| `submit` | reserve resources and perform an at-most-once frozen submission |
| `observe` | obtain scheduler terminal state and registered gate results |
| `stop-matrix` | atomically settle every never-submitted role after an exact upstream role is exhausted and failed |
| `cancel` | cancel one exact registered job under an authorized stop/abort rule |
| `recover` | consume the one reserved recovery attempt on the authenticated original node |
| `observe-recovery` | settle recovery accounting and authenticate exact target absence |
| `collect` | retrieve, hash, and sanitize package evidence |
| `clean` | remove exact registered ephemeral roots after collection proof |
| `close` | classify the run and emit the terminal summary |

Commands MUST be idempotent where the state and content identity already
match, except that an ambiguous `submit` MUST reconcile its unique submission
token and MUST NOT automatically resubmit. A collision with different content
MUST fail closed.

`cancel` accepts only an exact registered Slurm job ID. It MUST NOT select by
username, job-name pattern, or glob. It records scheduler acknowledgement,
observes the final terminal/accounting record, and never treats cancellation
alone as successful cleanup.

## 6. Normative records

Records MUST be UTF-8 JSON objects with LF line endings, a declared
`schema_version`, and no duplicate keys. Records are canonicalized with JSON
Canonicalization Scheme (RFC 8785/JCS); `record_sha256` is omitted before
canonicalization and hashing of the resulting UTF-8 bytes. Hashes MUST be
lowercase SHA-256. Timestamps MUST be UTC RFC 3339. Numeric byte counts and
resource limits MUST be integers. Implementations MUST reject duplicate keys
before canonicalization and validate records before acting on them.

There are two record classes:

- **private operational state** is mode-restricted, excluded from Git, and MAY
  contain exact paths, endpoint details, raw evidence locations, and other
  fields required for safe execution; and
- **publication receipts** are sanitized repository artifacts containing
  logical/run-relative paths, storage classes, path hashes, and verdicts, but
  no private fields.

Both classes bind the same `authority_id`, `run_id`, `package_id`,
`source_commit`, and `plan_id` when one exists. Private state MUST survive
through cleanup and exact job reconciliation, then be deleted using its
registered exact path and verified absent unless the package explicitly
authorizes restricted retention. It MUST NOT enter publication or ordinary
backups. The toolkit makes no physical secure-erasure claim for APFS, Ceph,
snapshots, or solid-state storage. Cleanup MUST NOT operate from a sanitized
path hash or publication receipt alone.

Every record contains:

- `schema_version`;
- `record_type`;
- `authority_id`;
- `run_id`;
- `package_id`;
- `source_commit`;
- `created_at`;
- `producer_version`; and
- `record_sha256`, computed over the canonical record with that field omitted.

`authority_id`, `resource_budget_id`, `run_id`, and `package_id` MUST match
`[a-z0-9][a-z0-9._-]{0,95}`. They MUST NOT contain usernames, paths, shell
metacharacters, whitespace, or unexpanded variables.

### Shell-facing value safety

Every identifier, relative path, scheduler value, and operation argument that
can cross an SSH or shell boundary MUST have a field-specific grammar.
General identifiers use the grammar above. Portable relative-path segments
MUST match `[A-Za-z0-9_][A-Za-z0-9._+=-]{0,254}`; paths are one or more such
segments separated by `/` and MUST NOT contain empty, `.` or `..` segments.
All shell-facing values MUST reject NUL, control characters, newlines,
carriage returns, unexpanded variables, and command substitution.

Toolkit-owned scripts receive values as positional arguments, quote every
expansion, and use `--` before path operands where the command supports it.
They MUST NOT use `eval`, construct executable command strings, interpolate
values into shell source, or treat data as options. Exact absolute paths exist
only in validated private state and are passed as quoted positional data.

### 6.1 Transition event

Every lifecycle transition writes an event with `transition_scope` (`run` or
`attempt`), `from_state`, `to_state`, `input_record_hashes`,
`result_record_hashes`, and `plan_id` when a plan exists. Attempt events also
contain job role and attempt index. Pre-plan events instead bind the authority,
cluster-profile, and capability-receipt hashes used by the transition. An
event is published only after its result records are durable.

### 6.2 Capability receipt

A capability receipt additionally records:

- scope: `control`, `login`, or `compute`;
- observation method and, for compute scope, frozen plan and Slurm job
  identity;
- OS, architecture, libc, CPU features, executable identities, scheduler,
  storage, accelerator, and network observations relevant to the plan;
- unavailable and untested capabilities separately; and
- capture time and maximum permitted planning age.

Receipts from different scopes MUST NOT be merged into one fact namespace.
Login observations cannot satisfy compute requirements. Expired receipts MAY
seed a probe but MUST NOT authorize a new commitment.

### 6.3 Run plan

The private run plan additionally records:

- authority source and allowed operation classes;
- immutable `authority_id` and `resource_budget_id`;
- exact starting branch, source commit, and push target;
- confirmation classification and prohibited data classes;
- an ordered provider stack, provider API versions, selection reasons, and
  validated `requires`/`provides` composition;
- target OS, architecture, libc floor, CPU baseline, interpreter ABI,
  framework/CUDA contract, and final runtime path where applicable;
- every immutable asset's logical name, bytes, hash, executable intent, source
  class, and license provenance for externally redistributable assets;
  repository-owned assets MAY reference repository license/provenance once;
- exact remote run root and permitted job-local root pattern;
- job matrix, typed GRES, partition, time/memory/CPU limits, cumulative
  resource ceiling, stop ladder, and retry classes;
- registered tests, their pass expressions, and one exact allowlisted
  structured gate-receipt path per job role;
- evidence allowlist and sanitization rules; and
- cleanup targets and prerequisites.

The plan identity changes if any field above changes. Environment variables,
current directories, scheduler defaults, and module defaults MUST NOT supply
undeclared plan semantics.

`plan_id` is the SHA-256 of the RFC-8785 canonical immutable semantic plan
payload. It excludes record metadata such as `created_at`,
`producer_version`, and `record_sha256`; rerendering unchanged semantics MUST
produce the same `plan_id`.

The initial plan is revision zero. A prospective amendment is a new immutable
plan-revision record containing `supersedes_plan_id`, amendment reason,
authorized changed fields, effective unstarted job roles/attempts, and hashes
of retained predecessor records. It MUST NOT change a started or completed
attempt, erase prior evidence, widen dispatch authority, or reset resource
use. Prior receipts remain valid under their original `plan_id`; the new
revision explicitly carries them forward by hash. An unauthorized mutation is
`PLAN_DRIFT`, not an amendment.

### 6.4 Transfer receipt

A transfer receipt records asset identity, source and destination classes,
method, partial name, verified byte count and hash, elapsed time, promotion
status, and cleanup status. Destination existence alone is never verification.

### 6.5 Submission intent and job receipt

Before `sbatch`, the toolkit atomically persists a private submission intent
containing the unique authority/run/plan/attempt token and reserves the full
requested resource charge in the append-only `resource_budget_id` ledger while
holding its authority-wide lock. An ambiguous intent remains fully charged
until non-submission is positively proven. A job receipt supersedes, but does
not erase, that intent.

A job receipt records the frozen job role and attempt index, Slurm job ID,
requested resources, node and accelerator classes, terminal state, exit code,
elapsed allocation, available accounting, registered gate results, and log
hashes. Missing accounting is recorded as unavailable, not zero.
For every terminal exit, including scheduler or application failure,
registered gate results MUST be parsed from the job role's exact regular,
nonsymlink gate-receipt file under the marked run root. A job wrapper MUST
atomically publish that receipt on every catchable exit before returning its
status. Scheduler state or controller-generated placeholder gates MUST NOT
substitute for that receipt. The controller records its content hash and
accepts only a nonempty string-to-boolean gate object.

### 6.6 Collection and cleanup receipts

A collection receipt binds the local evidence archive hash to the complete
job/transfer receipt set and the applied sanitization policy.

A private cleanup record contains each exact target and marker. Its sanitized
publication receipt records logical target, path hash, validation verdict,
command outcome, verified absence, reconciliation of exact registered job
identities, and retained recovery sources. Cleanup may occur only after a
valid collection receipt or an explicit package-authorized abort rule.

## 7. Provider contract

The provider API is versioned independently from toolkit and record versions.
Revision 1 recognizes these provider classes:

- `runtime`: module, portable interpreter, or source-built interpreter;
- `framework`: locked wheel/runtime closure such as PyTorch;
- `transport`: SCP, rsync, or a later managed transport;
- `scheduler`: Slurm command and accounting adapter;
- `storage`: durable, job-local, archive, and checkpoint behavior; and
- `accelerator`: typed device request and validation behavior.

A revision-1 provider is a declarative, committed record. The cluster profile
names an explicit ordered provider stack; revision 1 does not implement a
general dependency solver. A provider definition MUST declare:

- provider class, name, API version, and implementation version;
- supported control and target platform constraints;
- required commands and network phase;
- probe fields it consumes and emits;
- deterministic selection constraints plus machine-checkable `requires` and
  `provides` capabilities;
- assets and licenses it introduces;
- class-specific operation identifiers, typed request/response record types,
  and side-effect classes;
- typed failure codes; and
- capabilities it explicitly does not establish.

Operation identifiers map only to toolkit-owned committed implementations;
revision 1 does not execute provider-supplied commands. Operations that do not
apply to a class are omitted rather than represented by empty hooks. Every
operation MUST receive a validated request record and write a response record.
It MUST NOT edit the run plan, select a different provider, access confirmation
data, or exceed its declared side-effect class.

The toolkit validates the entire ordered stack before freezing the plan,
including Python ABI, target tag, libc floor, CPU baseline, CUDA runtime,
driver floor, framework ABI, and final paths. An incompatible stack fails
during planning before any provider operation starts.

Provider discovery MAY yield multiple candidates. Selection MUST be explicit
and deterministic under committed policy. If the selected provider fails, the
toolkit MUST stop. Trying another provider requires a new plan or prospective
amendment; provider order is not an implicit fallback ladder.

The foundation MUST support static in-repository providers. Executable or
dynamic external plugins, arbitrary code download, and registry-based plugin
installation are out of scope until a later major provider API defines
execution, trust, and signing.

## 8. Runtime and dependency rules

Runtime selection MUST distinguish:

1. discovered interpreter candidates;
2. selected interpreter distribution and ABI;
3. resolved dependency closure for the target platform; and
4. compute-validated environment capability.

An environment is not validated merely because resolution or installation
succeeds. Its plan MUST bind the target triple, libc floor, CPU baseline,
final extraction path, interpreter version/hash, dependency lock/hash, native
library contract, and registered compute tests.

For Lemhi:

- `rmm` is macOS arm64 and MUST NOT resolve native artifacts for itself when
  the target is Linux x86-64;
- login-built artifacts MUST NOT inherit the ambient architecture-targeted
  Spack compiler/runtime;
- a virtual environment MUST be created at its final path, or all entrypoints
  MUST be invoked through the selected interpreter with `python -m`;
- `PYTHONPATH`, `PYTHONHOME`, user site, loader paths, and activation state
  MUST be isolated and recorded;
- compute-node internet access MUST be assumed absent;
- wheels and runtime archives MUST be individually hash-pinned and verified;
- archives MUST be inspected before extraction and reject absolute or parent
  paths, escaping symlinks/hardlinks, device files, setuid/setgid entries, and
  unexpected ownership; extraction occurs with restrictive permissions only
  beneath the registered final root and is followed by manifest verification;
- compute validation MUST record loader/`ldd` dependencies, CPU baseline, and
  libc compatibility for native runtime components;
- source distributions and native compilation are prohibited unless the plan
  freezes a separately validated compute-safe toolchain/build operation;
- `pip check` or the provider's equivalent is necessary but not sufficient;
  and
- NumPy and other optional bridges MUST be explicit locked/tested dependencies
  before a claim relies on them.

Newer is not automatically preferred. A provider policy considers security
support, wheel availability, target compatibility, study reproducibility, and
the cost of prospective revalidation.

## 9. Transfer and storage rules

Small immutable objects SHOULD be archived before WAN transfer. Every upload
MUST land at a `.part` name or provider-equivalent nonfinal identity, then be
checked by byte count and SHA-256 before atomic promotion.

Every download MUST land at a nonfinal name inside private quarantine. The
toolkit compares frozen remote and local byte counts and SHA-256, then
atomically promotes the object within quarantine before extraction or
sanitization.

The toolkit MUST distinguish control-host transfer, durable cluster storage,
and job-local storage. It MUST label measurements as cold, warm, or unknown
and MUST NOT promote warm-cache diagnostics into throughput claims.

Every job-local storage provider MUST declare either `scheduler_purged` with a
documented lifecycle guarantee or `toolkit_recoverable` with an authorized
recovery mechanism. Persistent `/tmp` fallback is prohibited unless a later
allocation can locate, remove, and verify the exact registered path. A normal
job emits an in-allocation absence receipt after cleanup. Following timeout,
preemption, `SIGKILL`, or node loss, closure requires either the declared
scheduler-purge evidence or a successful recovery receipt; otherwise the run
ends `CLEANUP_INCOMPLETE` and retains private recovery state.

Checkpoint publication MUST declare whether it proves atomic visibility,
filesystem synchronization, application restart equivalence, or power-loss
durability. These are separate capabilities.

Shared filesystem availability MUST NOT be represented as account quota.

Collected raw evidence MUST first enter an allowlisted, size-bounded,
mode-restricted local quarantine. Before extraction, the toolkit rejects
nonregular files, absolute/parent paths, escaping links, devices, unexpected
ownership/modes, and archive expansion beyond the frozen byte/file ceilings.
Sanitization writes a separate publication tree. Private manifests bind raw
and sanitized hashes; only the sanitized tree may be published. Quarantine is
removed after verified publication unless the package explicitly authorizes
restricted retention.

If collection fails after a raw download has been promoted, a retry MUST NOT
overlay or reuse that quarantine. The toolkit atomically retains the non-empty
directory under a failed-attempt identity, creates a fresh mode-restricted
quarantine, and repeats authenticated download and extraction from scratch.

## 10. Scheduler and resource rules

Slurm submissions MUST use committed scripts and explicit partition, typed
GRES, CPU, memory, time, output, and error settings. The toolkit MUST:

- parse typed GRES into resource, accelerator model, and positive count before
  remote mutation; require the provider request and model to match; require
  that count to equal the plan's `gpus` accounting multiplier; and reject a
  count above the provider-declared single-node maximum;
- verify current eligibility and device inventory before first submission;
- create output directories before `sbatch`;
- default to `--no-requeue`; requeue requires prospective registration and
  accounting for every allocation/restart;
- hold both the per-run and authority-budget locks, atomically persist a
  submission intent, and reserve its full requested charge in the append-only
  shared ledger before invoking `sbatch`;
- derive a unique token from `plan_id`, job role, and prospective attempt index,
  then place it in a supported queryable Slurm field and bounded job name;
- use `sbatch --parsable` and atomically register every returned job ID before
  releasing the lock;
- on missing, malformed, or interrupted output, reconcile `squeue` and `sacct`
  by the unique token before any retry; if exactly one job cannot be proven,
  return `SUBMISSION_OUTCOME_UNKNOWN` and prohibit automatic resubmission;
- maintain requested and actual GPU-minute ledgers separately;
- prevent submission that would exceed the frozen cumulative ceiling;
- implement the package's sequential/parallel and stop ladder exactly;
- classify terminal state from Slurm accounting plus the authenticated exact
  allowlisted gate receipt registered for that job role;
- treat absent GPU memory, energy, or child-process accounting as unavailable;
  and
- wait for terminal accounting to settle, count every registered requeue or
  restart when allowed, and reconcile exact owned job IDs before closure.

Requested GPU-minutes are allocated GPU count multiplied by requested time
limit and are reserved at submission intent. Settled accounting records exact
allocated GPU-seconds as GPU count multiplied by Slurm `ElapsedRaw`; the
integer actual-GPU-minute ledger rounds that value up to the next minute. It
does not derive from missing child-process or device telemetry. Arrays and
multi-allocation jobs require an explicit prospective accounting policy or
are rejected.

The multiplier in both calculations is the same count authenticated from the
typed GRES. A plan such as `gpus: 1` with `gres: gpu:l40:4` is invalid rather
than a request for four devices charged as one. Recovery has the identical
equality and provider-maximum requirements. Optional single-node multi-GPU
providers do not change the canonical one-GPU default and must state their
topology and maximum explicitly.

The ledger is keyed by `resource_budget_id`, not `run_id` or `plan_id`, and is
shared across every run, plan revision, attempt, retry, cancellation, and
recovery action under the dispatch. No new run or amendment may reset consumed,
reserved, or ambiguity-held use.

An exit code of zero is not a pass without every registered gate. An expected
nonzero code MAY be a pass only when prospectively registered and supported by
the required evidence.

## 11. Destructive-action and data firewalls

The toolkit MUST exclusively create the registered remote root and atomically
install its ownership marker before placing any other object. The marker binds
`run_id`, `package_id`, plan hash, source commit, and exact canonical root.
Creation and staging hold a run-specific lock. A package-authorized abort path
MUST cover interruption before submission, including before marker
publication, without widening the target. An abort after staging revalidates
the exact marker and plan identity, removes only the registered durable root,
proves absence, and records job-local state as `not_started`.

Cleanup MUST perform marker validation, canonical ancestor and symlink checks,
and deletion inside one bounded remote script while holding the run lock. It
MUST re-read and validate the marker immediately before deletion.

Cleanup MUST reject:

- empty, relative-after-resolution, symlink-escaped, or unregistered targets;
- `/`, `$HOME`, `~`, a home root, repository root, shared project root, or
  unresolved variable;
- a target whose marker or canonical path differs from the plan; and
- recursive glob or prefix-derived target sets.

Confirmation classification and a default-deny logical-object allowlist are
required authority inputs before any filesystem observation. Core commands
and providers—including `doctor`, `probe`, `prepare`, transfer, and
collection—MUST validate paths against them before enumerating, invoking
filesystem metadata operations, hashing, archiving, or reading content.
Unregistered globs, directory walks,
symlink or hardlink traversal, archive-member inclusion, and metadata
inspection across protected roots are prohibited. Capability tooling MUST NOT
enumerate, hash, sample, or infer protected confirmation targets.

## 12. Error model

Errors are typed and stable within a record major version. Required classes
include:

- `AUTH_BOOTSTRAP_REQUIRED`;
- `AUTHORITY_INVALID`;
- `ALLOWLIST_VIOLATION`;
- `CAPABILITY_STALE`;
- `CAPABILITY_SCOPE_MISMATCH`;
- `PLAN_DRIFT`;
- `PROVIDER_UNAVAILABLE`;
- `PLATFORM_MISMATCH`;
- `ASSET_IDENTITY_MISMATCH`;
- `TRANSFER_INCOMPLETE`;
- `RESOURCE_CEILING`;
- `SUBMISSION_OUTCOME_UNKNOWN`;
- `JOB_TERMINAL_MISMATCH`;
- `GATE_FAILED`;
- `EVIDENCE_INCOMPLETE`;
- `SANITIZATION_FAILED`;
- `ARCHIVE_UNSAFE`;
- `RUN_LOCKED`;
- `CLEANUP_TARGET_INVALID`; and
- `CLEANUP_INCOMPLETE`.

Errors MUST identify the failed operation and safe next action without
printing secrets, unrestricted environments, or unsafe destructive commands.

## 13. Versioning and compatibility

Toolkit release, provider API, record schema, cluster profile, and scientific
work-package versions are independent axes.

- Adding an optional record field requires a minor schema revision.
- Removing, renaming, or changing semantics requires a major schema revision.
- A consumer MUST reject an unsupported major version.
- A provider API major mismatch MUST fail before its operation executes.
- Cluster profiles and provider definitions are content-hashed inputs to the
  run plan.
- A toolkit upgrade MUST NOT reinterpret or rewrite historical receipts.

## 14. Minimum vertical slice

Foundation execution implements only the smallest end-to-end mechanics:

1. executable command paths for every lifecycle operation;
2. local authority/config validation and `doctor`;
3. warm-master check with no interactive fallback;
4. separate sanitized login and fixture-simulated compute receipts;
5. deterministic plan creation from one static cluster profile and explicit
   declarative provider stack;
6. SCP `.part`/hash/promotion execution through an injected fake command
   adapter; rsync remains a later provider;
7. Slurm submission reservation, unique-token reconciliation, script
   rendering, authority-wide resource-ledger enforcement, multi-attempt state,
   cancellation, and prospective plan revision through injected fakes;
8. private evidence quarantine, allowlisting, and sanitized publication;
9. failure-atomic ownership-marker and cleanup execution against safe
   temporary fixtures; and
10. closeout classification from synthetic job/gate receipts.

All production command paths MUST execute in foundation tests, but injected
command adapters and temporary fixtures replace live SSH, Slurm, and remote
storage. The foundation MUST NOT require a live remote write or allocation to
pass. The separately dispatched Python 3.11 smoke is the first live validation
of already implemented paths and supplies its own resource authority.

## 15. Acceptance tests

The implementation package MUST include deterministic positive and adverse
fixtures proving at least:

- unavailable SSH masters yield `AUTH_BOOTSTRAP_REQUIRED` without prompting;
- master expiry immediately before or during a remote operation fails without
  cold reconnection;
- login and compute receipts cannot satisfy each other's requirements;
- `probe` cannot allocate without a frozen bounded plan;
- stale capability data cannot authorize a commitment;
- Mac arm64 assets cannot satisfy Linux x86-64 plans;
- incompatible ordered runtime/framework requirements fail during planning;
- provider failure cannot trigger implicit fallback;
- unauthorized plan mutation changes identity and invalidates downstream
  receipts, while a valid amendment preserves declared predecessor lineage;
- RFC-8785 golden records from independent serializers have identical hashes,
  including Unicode and escaped strings;
- partial or hash-mismatched transfer cannot promote;
- a download cannot leave quarantine's nonfinal identity until remote/local
  size and hash match;
- unsafe runtime/evidence archive members cannot extract;
- an over-ceiling job cannot be submitted or rendered as authorized;
- concurrent submitters serialize; accepted-but-response-lost reconciles by
  token or stops at `SUBMISSION_OUTCOME_UNKNOWN` without resubmission;
- two different runs under one `resource_budget_id` cannot independently
  reserve the same remaining authority budget;
- sequential, parallel, retry, cancellation, and expected-nonzero attempts
  follow independent attempt lifecycles and settle the run matrix correctly;
- a plan amendment preserves completed evidence and cumulative use, changes
  only authorized unstarted work, and cannot reset the authority budget;
- shell-facing metacharacters, newlines, leading dashes, substitutions, and
  unsafe path segments are rejected before operation rendering;
- exit zero plus a failed registered gate is not a pass;
- missing accounting stays unavailable rather than becoming zero;
- unsafe, symlink-escaped, unmarked, concurrently replaced, or mismatched
  cleanup targets are refused, including interruptions at each stage boundary;
- hard-killed or preempted job-local cleanup requires declared purge evidence
  or authorized recovery and otherwise yields `CLEANUP_INCOMPLETE`;
- protected direct paths, globs, directory walks, symlinks, hardlinks, and
  archive members are rejected before content or metadata observation;
- evidence sanitization catches forbidden identities and paths, publication
  receipts cannot leak private fields, and cleanup refuses sanitized-only
  state; and
- historical receipts remain readable but immutable across a minor toolkit
  upgrade.

Repository gates from `AGENTS.md` also apply. Production functions added under
`crates/` trigger the coverage/CRAP gate from their first implementation.

## 16. Historical foundation sequence

1. Execute the toolkit-foundation implementation and fixtures against this
   specification.
2. Scaffold and execute a separate CPython 3.11 Lemhi smoke package using a
   pinned exact CPython patch/distribution/hash, Linux x86-64 libc/CPU
   contract, final path, license, and binary-only offline wheel closure. It
   must validate on a compute node: `ssl`, `sqlite3`, `ctypes`, `venv`,
   subprocess, multiprocessing, native-extension linkage, NumPy operations,
   PyTorch-to/from-NumPy conversion, isolated Python/loader paths, no-network
   reconstruction, one-L40 tensor/autograd/checkpoint behavior, and exact
   remote/job-local cleanup within a prospectively frozen resource ceiling.
   Its terminal excludes performance, multi-GPU, requeue, production
   durability, and A10M3 scientific claims.
3. Dispatch A10M3 only after both the toolkit foundation and Python 3.11 smoke
   reach their registered ready terminals. A10M3 remains a separate scientific
   package, binds the current configuration governed by
   `SPEC-LEMHI-CANONICAL-CONFIGURATION`, and retains the confirmation firewall.

## 17. Revision-2 operational hardening

This section is normative and supersedes revision-1 language where the two
conflict. Revision-1 records, providers, and completed runs remain readable
without reinterpretation. New hardened runs MUST use
`lemhi-toolkit-record-2`, producer `lemhi-toolkit-hardening-2`, and an ordered
all-v2 provider stack under `lemhi-toolkit-provider-2`. A v2 execution stack
MUST NOT mix v1 providers. The recognized classes are `runtime`, `framework`,
`transport`, `scheduler`, `storage`, `accelerator`, and `toolchain`.

### 17.1 Authority revisions and ledger lifecycle

A live v2 authority binds the absolute private ledger anchor, genesis hash,
starting branch, push target, immutable resource class and ceiling, published
source lineage, scheduler authority token, and last reviewed ledger-head
checkpoint. The live CLI derives the anchor from authority and MUST NOT accept
an arbitrary state root.

Only a separately authorized `initialize-authority` operation may create
genesis. It MUST atomically prove the canonical anchor absent, prove no
predecessor or scheduler/resource evidence exists, create genesis, and bind
its path and hash into the authority. `derive-run` creates an immutable
authority revision and run seed while preserving authority, package, budget,
resource class, ceiling, branch, and push target. It accepts only an already
published source commit and binds predecessor hashes. It cannot initialize a
ledger, submit, allocate, amend a completed attempt, or reset accounting.

Published authority revisions checkpoint reviewed ledger heads. Missing,
malformed, copied, truncated-before-checkpoint, alternate-path, or
caller-stale state fails. Before every live reservation or submission, exact
scheduler accounting keyed by the immutable authority token MUST reconcile
against the ledger. Unavailable, ambiguous, missing, or restoration-indicating
accounting holds before spending. A local chain cannot by itself detect
wholesale restoration of both the ledger and its local head to a valid prefix;
the toolkit MUST disclose this trust boundary and MUST NOT claim otherwise.

### 17.2 Toolchain, layout, and environment closure

The v2 `toolchain` provider binds coupled executables, target standard
libraries, compiler/runtime paths, target platform, licenses, offline rule,
archive/layout assertions, loader checks, and registered build smoke. A Rust
closure includes exact `cargo`, `rustc`, target standard library, host C/C++
compiler, Cargo vendor root relative to extracted source, and offline metadata
and build probes. Controller prepare validates archive layout, safe extraction,
and vendor relationships. Compute preflight validates exact versions, paths,
loader resolution, compiler invocation, and bounded build smoke. Presence
alone is never sufficient, and providers remain declarative data.

The v2 plan declares `required_job_environment`. Slurm starts with
`--export=NONE` or a provider-proved equivalent, but this flag is not proof
that the site wrapper exported no Python or loader variables. The job wrapper
records typed presence flags only, clears prohibited ambient variables,
reconstructs registered Slurm/device variables and exact public operational
values, then asserts the closed environment before the first interpreter
import. A value that survives clearing or conflicts with the reconstructed
contract is an ambient override and fails. Evidence publishes only allowed
names and safe values or value hashes, never ambient values. Deterministic
CUDA work requires `CUBLAS_WORKSPACE_CONFIG=:4096:8` before the first
Python/framework import.

### 17.3 Job-local admission, supervision, and recovery

A provider-v2 plan MAY declare an `admission_materialization` contract for
package-specific pre-submission checks. The contract binds a frozen executable
asset, an allowlisted controller receipt directory, the authenticated record
type, and the exact required role matrix. For every covered role, `submit`
MUST, while holding the existing run lock and before reserving resources,
authenticate the role receipt and require its package, authority, run, source,
plan, role, attempt, PASS gates, and private toolkit-state SHA-256 to match the
then-current state. A missing or stale receipt fails before ledger reservation
or scheduler submission. A package materializer may execute outside the lock,
but it cannot authorize a later state because `submit` performs this
current-state check atomically with the transition.

New v2 storage providers use `toolkit_recoverable`; `scheduler_purged` is
historical-only and cannot authorize a hardened plan. Primary admission
reserves both primary charge and a frozen recovery contingency. Recovery
attempts, resources, wall time, retries, exact-node rule, and stop conditions
are fixed prospectively. Ambiguous cleanup retains the reserve; verified
absence releases it.

Admission accepts only provider-declared canonical job-local bases with
filesystem, owner, and permission assertions. Required bytes and inodes cover
expanded assets, products, checkpoints, a fixed margin, and a minimum free
floor. Claims serialize per base and recheck before major expansion. Capacity
or cleanup failure never authorizes deletion of unrelated content.

Every attempt uses a content-addressed immutable path and marker binding
authority, budget, run, plan revision, role, attempt, scheduler job ID, node,
base, target, and UID. The toolkit process supervisor creates a child process
group, forwards catchable signals, waits for children/steps, writes durable
status atomically, performs local cleanup even when publication fails, and
records absence. Cleanup or status uncertainty dominates application exit as
`CLEANUP_INCOMPLETE`.

Recovery derives the node only from authenticated terminal accounting and
first proves the original job, all steps, and requeues absent from `squeue`
and settled in `sacct`. On that node it validates UID, marker, ancestors,
filesystem identity, and canonical target twice, runs one exact bounded
deletion, and proves absence. Any unavailable node, accounting ambiguity,
marker/path drift, or failed proof remains `CLEANUP_INCOMPLETE`.

The frozen recovery contingency declares its exact script asset, partition,
typed GRES, GPU count, CPUs, memory, wall time, gate receipt, and the fixed
`slurm/toolkit-recovery.0.{out,err}` evidence paths. Its GPU-minute charge MUST
equal GPU count times wall-time minutes, and v2 currently admits exactly one
attempt. `recover` is legal only after the source attempt is terminal and its
authenticated gate receipt says `job_local_cleanup=false`; it reconciles the
whole authority before submission and consumes the existing reserve rather
than creating a new charge. `observe-recovery` requires successful scheduler
accounting, exact-node agreement, the original job identity, the target-path
hash, and all registered recovery gates before cleanup can continue.

The recovery contingency is immutable across plan amendments. Planned attempt
streams and the fixed recovery streams have one global ownership namespace:
duplicate stream writers are invalid, and no planned or recovery gate receipt
may alias any stream in that namespace. Initial planning and every amendment
MUST enforce the same complete collision check.

### 17.4 Evidence projection

Collection authenticates a private `RAW_COLLECTED` record before publication
projection. It binds raw hashes, exact gates, and cleanup-authorizing marker
data. Projection failure holds publication without erasing cleanup authority,
and projection cannot change gate results.

Text projection rejects invalid UTF-8 and deterministically escapes every raw
reserved angle-bracket token to `[[RAW_RESERVED_TOKEN:NAME]]` before applying
typed replacements. The private receipt counts those escapes. This prevents
third-party placeholders from masquerading as toolkit-authored tokens while
preserving their diagnostic meaning. Typed replacements are ordered by
descending byte length and replace paths only when they are exact or
descendants—not sibling prefixes. JSON is parsed with
duplicate-key rejection and transformed structurally by field type. Scientific
JSON admits finite integer and floating-point values but rejects NaN, Infinity,
and overflow to a non-finite value; authority, ledger, plan, and receipt
canonicalization retains its stricter no-float rule. Binary evidence is allowed
unchanged only by exact schema/hash or excluded. Provider-v2 collection treats
plan-allowlisted `.npz` and `.pt` evidence as exact-byte binary projections
under sanitizer version `lemhi-evidence-projection-5`:
typed text replacements are not applied, raw and projected hashes must be
identical, and the forbidden-value byte scan still runs. The private transformation
receipt binds sanitizer version, token counts, sanitized hashes, and raw-parent
hashes. The forbidden-value scan runs after projection and rejects unknown
sensitive material. Evidence producers SHOULD use non-reserved notation for
diagnostic redactions; third-party reserved-looking placeholders are escaped,
never interpreted as authorized redactions.

### 17.5 Transfer telemetry and immutable manifests

V2 transfer receipts record integer `elapsed_ns`, bytes, method, final
identity, and exactly one state: `uploaded`, `resumed`, or
`already_verified`. Integer rate computation MUST be overflow-safe. A skip
immediately revalidates remote identity. Resume is allowed only when the
provider proves range integrity; otherwise an SCP partial is verified and
atomically replaced or removed before full retry. SSH masters are rechecked
before transfer and after long transfers.

Within one authority/run lineage, assets use content-addressed immutable
identities and an append-only revision manifest. Same-name/different-hash and
parallel claims serialize or fail deterministically; referenced identities
cannot be overwritten. Cross-run and cross-authority caching remains excluded
until quota, ownership, concurrency, garbage collection, and licensing are
separately designed.

### 17.6 Canonical transition

Configuration semantics, smoke evidence, and designation are separate
immutable records. Successor semantics use
`lemhi-canonical-configuration-semantics-2`; a separately dispatched bounded
smoke produces `lemhi-canonical-smoke-attestation-1`; only a later
`lemhi-canonical-designation-index-1` revision may change which immutable hash
is current. Historical v1 status means status at issuance. Failed smoke holds
without mutating any record or falling back to v1 storage semantics.

The required forward sequence is A10M4O1 hardening, immutable successor
semantics, bounded smoke, immutable attestation, designation-index revision,
then A10M5. The 5x/10x scientific runtime thresholds are outside this revision
and remain unchanged.

### 17.7 Terminal failure closure

For provider API v2, `stop-matrix` MAY settle all planned zero-attempt roles
only when an exact trigger role is exhausted after one or more authenticated
failed `RESULT_VALIDATED` attempts, every existing attempt is settled, and all
attempted roles are passed or exhausted. Before writing the stop, the toolkit
MUST reconcile the full scheduler authority against the append-only ledger,
hold the authority-budget lock before the run lock, and require the fixed
reason `upstream-role-exhausted`. The receipt binds the trigger's job-receipt
hashes, the current plan, ledger head, and complete stopped-role set. Selective
waiver is prohibited until the plan schema prospectively defines dependency
edges.

A stopped role is classified `NOT_EXECUTED_UPSTREAM_FAILURE`. It is not an
attempt, job receipt, cancellation, successful gate, retry, resource charge,
or scientific result. The stop is immutable and idempotently republishable
within the run. `MATRIX_SETTLED` MAY include passed roles, exhausted attempted
roles, and the exact stopped-role set. Cleanup MUST require registered
job-local cleanup evidence for every submitted role and MUST skip only stopped
roles that have no attempt. A stop can never suppress cleanup ambiguity from a
started role.

The plan's `evidence_allowlist` is a maximum permitted member set, not a claim
that every member exists on all terminal paths. Remote collection MUST report
a sorted, disjoint present/absent partition of that exact set, archive exactly
the present regular nonsymlink single-link members, fail if none are present,
and retain the existing local archive safety, size, ownership, projection, and
unexpected-member checks. The controller MUST compare archive members to the
reported present set. For every submitted attempt, its exact registered gate
receipt and Slurm stdout/stderr remain mandatory, and the collected gate hash
MUST equal the hash authenticated by `observe`. Missing evidence remains
visible in job and matrix-stop receipts; collection MUST NOT create placeholder
admissions, gate receipts, or science results.

If the reserved recovery was invoked, sparse collection additionally requires
the recovery to be `RESULT_VALIDATED`, its configured gate receipt, both fixed
recovery Slurm streams, and a valid gate hash authenticated by
`observe-recovery`. The collected recovery gate hash MUST match that observed
identity, and every recovery gate result MUST be included in the private
`RAW_COLLECTED` record. An unused released reserve creates no recovery evidence
obligation.
