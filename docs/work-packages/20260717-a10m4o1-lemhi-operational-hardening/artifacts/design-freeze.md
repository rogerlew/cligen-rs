# A10M4O1 prospective design freeze

Frozen for dual review before implementation, remote mutation, or allocation.

## Ownership boundary

The toolkit owns authority, plans, providers, transport, scheduler adapters,
evidence lifecycle, publication projection, job-local lifecycle, resource
ledger, and exact cleanup mechanics. A package owns scientific data semantics,
model state, checkpoint contents, output-format validity, and its boolean
gates. The guide connects the two with authoring checklists; the toolkit must
not infer application meaning from filenames, tensors, calendars, or exit
codes.

## Version freeze

Hardening is an explicit major transition:

- provider API `lemhi-toolkit-provider-2` adds the `toolchain` class and the
  hardened forms of `runtime`, `framework`, `transport`, `scheduler`,
  `storage`, and `accelerator`; a v2 execution stack cannot mix v1 providers;
- new events use record schema `lemhi-toolkit-record-2` and producer
  `lemhi-toolkit-hardening-2`; the reader continues to verify v1 records
  without reinterpretation, but new hardened runs write v2 only;
- successor configuration semantics use
  `lemhi-canonical-configuration-semantics-2`, smoke evidence uses
  `lemhi-canonical-smoke-attestation-1`, and the current/superseded pointer
  uses `lemhi-canonical-designation-index-1`; and
- every serialization is canonical JSON with integers for durations, sizes,
  counters, and rates. Floating-point timing and rate values are forbidden.

## Contract changes

### 1. Authority revision and anchored ledger

Add a `derive-run` command that consumes an existing private authority/budget
record plus an explicit new `run_id`, run-relative root, published source
lineage, asset manifest, and plan input. A new immutable authority revision
preserves authority ID, package, resource class, ceiling, starting branch, and
push target; it may add only an already-published source commit and predecessor
hashes. The run binds the authority-revision hash, not a mutable authority
file. An unpushed commit, wrong branch, wrong resource class, changed ceiling,
substituted identity, or exhausted budget fails closed.

The live adapter takes no arbitrary `--state-root`. Each authority binds one
canonical private ledger anchor: absolute path identity, genesis hash, and
append-only hash chain. A genuinely new operator dispatch authorizes exactly
one exclusive `initialize-authority` operation. It proves the canonical path
absent, proves no predecessor or scheduler/resource evidence exists for the
authority token, creates genesis atomically, and binds path and genesis hash
in the immutable authority record. Duplicate genesis or initialization by
`derive-run` is forbidden.

Published authority revisions checkpoint the last reviewed ledger head.
Missing, malformed, copied, truncated before that checkpoint, alternate-path,
or caller-stale state fails. Before every live reservation or submission, the
adapter also reconciles exact scheduler/accounting records carrying the
immutable authority token against the ledger. Unavailable or ambiguous
accounting, missing events, or evidence of restoration yields an authority
hold and requires an operator-reviewed authority revision before further
spending.

This contract does **not** claim that a local chain and local saved head can
detect wholesale same-path restoration to an internally valid prefix after
the last published checkpoint. That case is outside their trust boundary;
safety comes from mandatory external scheduler reconciliation, and failure to
complete that reconciliation holds rather than spends. A future trusted
monotonic-head backend may strengthen detection but is not assumed here. Test
adapters may inject temporary anchors explicitly marked non-live. Derivation
cannot create authority, amend completed attempts, copy private paths into
publication, allocate, or submit.

### 2. Toolchain and layout closure

The v2 `toolchain` provider declares every coupled executable, target platform,
archive member/layout assertion, compiler/runtime path, license provenance,
offline-network rule, and exact registered smoke. A Rust provider binds
`cargo`, `rustc`, the target standard library, host C/C++ compiler, Cargo
vendor root relative to the extracted source, and an offline metadata/build
probe. File presence alone is insufficient.

Package assets may declare data-only layout assertions using safe relative
paths and regular-file/directory types. The toolkit validates archive layout,
vendor relationships, and safe extraction on the controller during prepare,
then validates extracted paths, exact tool versions, loader resolution,
compiler invocation, and a bounded build smoke on the compute node. It never
executes provider-supplied shell text.

### 3. Deterministic job environment

The semantic plan gains an allowlisted `required_job_environment` map with
field-specific name/value grammars and a sensitivity classification. Slurm is
invoked with `--export=NONE` or a provider-proved equivalent. The
toolkit-owned wrapper reconstructs only registered Slurm/device variables,
sets exact `PATH`, compiler, cache, temporary-directory, and required public
operational values, and rejects ambient overrides. Receipts record the
sanitized environment contract with allowlisted names and value hashes unless
a value is explicitly safe and required for reproduction.

Deterministic CUDA plans require `CUBLAS_WORKSPACE_CONFIG=:4096:8`; the wrapper
sets it before the first Python or CUDA-framework import. Omission, override,
or import before environment closure fails before application work.

### 4. Job-local admission, supervision, and recovery

The v2 storage provider declares `toolkit_recoverable`, not
`scheduler_purged`. The primary submission reserves both its own budget and a
frozen recovery contingency. The contingency fixes the maximum recovery
attempts, node/resource shape, wall time, retries, and stop conditions. It is
released only after verified primary cleanup; ambiguous state keeps it
reserved.

Admission accepts only provider-declared job-local bases with canonical path,
filesystem, owner, and permission assertions. It calculates required bytes
and inodes from expanded manifests, outputs, checkpoints, and a fixed margin,
enforces a minimum free-space floor, serializes claims per base, and rechecks
before major expansion. A capacity or cleanup `ENOSPC` cannot authorize
deletion of unrelated content.

Each attempt receives a content-addressed immutable path and owner marker that
binds authority, budget, run, plan revision, role, attempt, scheduler job ID,
node, canonical base/target, and UID. The per-run manifest is append-only;
referenced identities are neither overwritten nor deleted by later revisions.
The toolkit wrapper is a process supervisor: it creates a child process group,
forwards catchable signals, waits for child and steps, writes durable status
atomically, performs local cleanup even when status publication fails, and
then records cleanup proof. Cleanup or status uncertainty dominates the
application exit and yields `CLEANUP_INCOMPLETE`.

Recovery derives the node only from authenticated terminal scheduler
accounting. It first proves the original job, all steps, and requeues are
absent from `squeue` and settled in `sacct`. On the exact node it validates
UID, marker, every ancestor, filesystem identity, and canonical target twice,
then runs one frozen bounded deletion script and proves absence. An
unavailable node, ambiguous accounting, path drift, marker mismatch, or
failed proof remains `CLEANUP_INCOMPLETE`; no command selects targets by job
name, prefix, username, glob, or process inspection.

### 5. Evidence collection and safe publication

Authenticated collection first creates a private `RAW_COLLECTED` record before
any publication projection. It binds raw hashes, applicable gate results, and
the exact cleanup-authorizing marker data. Thus projection failure produces a
generic publication hold without erasing the evidence needed for exact
cleanup. Projection cannot change gate results.

A private typed replacement map is derived only from registered controller,
remote-run, job-local, endpoint, and identity fields. Reserved token syntax is
rejected in raw text. Replacements are ordered by descending byte length with
deterministic numbering; path replacements match only an exact path or its
descendants, not sibling prefixes. Non-path fields use their declared type.
Invalid UTF-8 is rejected. Structured JSON is parsed with duplicate-key
rejection and transformed by field type rather than textual substitution.
Binary evidence is either admitted unchanged by exact hash/schema or excluded.

The transformation receipt records sanitizer version, per-token counts,
sanitized hashes, and private raw-parent hashes. The existing forbidden-value
scan runs after projection and rejects any unknown secret/path. Pre-existing
tokens, nested and sibling roots, duplicate roots, overlap, malformed JSON,
invalid UTF-8, and nondeterministic output all fail closed.

### 6. Transfer telemetry and bounded reuse

Every stage result records integer `elapsed_ns`, bytes, method, final identity,
and one of `uploaded`, `resumed`, or `already_verified`. Integer rate
derivation is overflow-safe. Timeout budgets use bytes, a conservative integer
minimum rate, and a fixed handshake allowance; they are operational bounds,
not throughput promises.

`already_verified` requires immediate remote identity revalidation. `resumed`
is permitted only when the selected provider proves range integrity; otherwise
a partial SCP object is verified and atomically replaced or removed before a
full retry. Reused SSH control masters are rechecked before transfer.

Within one authority/run lineage, content-addressed immutable assets stage
once and registered matrix jobs consume the verified identity. A plan revision
adds only new identities to the append-only manifest. Same-name/different-hash,
parallel claims, timeout, and mixed-revision cases fail or serialize
deterministically. Cross-run/cross-authority caching is deferred until quota,
ownership, garbage collection, concurrency, and licensing receive a separate
design; A10M4O1 does not claim that stage-once semantics fix the observed
multi-run retransfers.

## Documentation changes

The compute guide receives an A10M4 operational-hardening section covering:

- full controller/compute toolchain and extracted-layout preflights;
- sanitized deterministic environments and the pre-import CUBLAS requirement;
- capacity claims, process supervision, recovery reserve, scheduler liveness,
  and the falsified scheduler-purge assumption;
- stable authority revisions, exclusive ledger genesis, published head
  checkpoints, and pre-spend scheduler reconciliation;
- raw collection versus sanitized-publication behavior;
- within-run stage-once planning and the explicit cross-run-cache defer; and
- application-owned checklists for missingness, checkpoint cursor/device
  state, and format-aware output completeness.

The toolkit README gains concise examples for `derive-run`, deterministic
environment closure, recovery, evidence projection, and per-run matrix reuse.
The authoritative toolkit specification is amended before code and explicitly
reconciles every implementation delta found by A10M4.

## Canonical configuration transition

`lemhi-a10-py311-l40-v1` remains byte-immutable historical authority. Its
embedded status means status at issuance; it is never edited to express a
later designation.

Execution creates a new immutable semantic candidate under
`lemhi-canonical-configuration-semantics-2`, containing no mutable promotion
status or smoke-result field. A separately dispatched bounded Lemhi smoke
emits an immutable `lemhi-canonical-smoke-attestation-1` that binds the exact
candidate hash. Only a subsequent versioned
`lemhi-canonical-designation-index-1` revision may designate that hash current
and the former hash superseded. A failed smoke preserves both the candidate
and failed attestation, records a hold, and cannot silently fall back to v1.

The exact roadmap sequence is: hardening implementation; immutable semantic
candidate; bounded smoke; immutable smoke attestation; canonical designation
index revision; A10M5. Fixtures prove neither a failed smoke nor later
designation can mutate the candidate, attestation, or v1.

## Fixture matrix

Fixtures must prove:

1. missing `rustc`, target standard library, compiler, vendor root, loader
   closure, or controller/compute layout relation fails before science;
2. hostile ambient environment, missing/overridden deterministic values, and
   early Python import fail while exact `--export=NONE` rendering passes;
3. insufficient bytes/inodes, concurrent claims, expansion growth, and cleanup
   `ENOSPC` fail without deleting foreign content;
4. application exit, wrapper failure, status-write failure, `TERM`, and
   registered preemption signals obey process-group forwarding, exit
   precedence, atomic status, and catchable cleanup; simulated `KILL` cannot
   close without recovery;
5. primary admission reserves frozen recovery capacity; ambiguous primary
   state retains it; settled exact-node recovery charges the shared budget and
   validates scheduler liveness, UID, marker, ancestors, filesystem, and path;
6. first genesis succeeds once; duplicate genesis, alternate paths, malformed
   chains, old prefixes before a published head, wrong/unpushed source, and
   wrong branch/class/budget fail; restoration of ledger plus local head is
   exposed by injected scheduler evidence or holds when exact reconciliation
   is unavailable, while the design records the same-domain detection limit;
7. raw collection survives projection failure, exact cleanup remains
   authorized, gate results cannot change, and transformation receipts bind
   parents, hashes, counts, and sanitizer version;
8. nested/sibling/duplicate/overlapping roots, prefix paths, pre-existing
   tokens, malformed or duplicate-key JSON, invalid UTF-8, unknown forbidden
   values, and repeated projection exercise deterministic fail-closed rules;
9. integer transfer receipts reject overflow, revalidate skips, safely handle
   SCP partials, and recheck control masters; parallel/same-name-different-hash,
   timeout, and mixed-revision asset cases preserve immutable manifests;
10. v1 records/providers remain byte-immutable and readable, new runs emit
    exact v2 records only, and mixed v1/v2 execution stacks fail;
11. candidate semantics, smoke attestation, and designation index are separate
    immutable objects; failed smoke cannot promote or mutate any object; and
12. no fixture invokes live SSH, Slurm, GPU, protected data, or remote cleanup.
