# C3+3 Lemhi GPU computing for agents

This is the operational runbook for agent-driven Lemhi GPU work from `rmm`.
It consolidates the live evidence from A10M2, A10M2D1, the CPython 3.11
toolkit smoke, canonical-v2 qualification, and A10M4O2 operational acceptance.
Live cluster state was observed on 2026-07-16 and 2026-07-17 and must be
rechecked before each new resource commitment; public C3+3 documentation has
demonstrably drifted.

## Agent authoring authority

**Directive: agents have explicit authoring authority for Lemhi GPU work.**
Within an operator-approved scientific objective, agents may create and edit
repository documentation, work packages, Slurm scripts, CUDA/Python smoke
tests, staging and cleanup scripts, manifests, evidence records, roadmap and
catalog entries, and bounded corrective successor packages. Agents do not
need a separate permission request for ordinary, reversible repository
authoring or for completing the evidence and administrative follow-through of
an authorized package.

An execution dispatch additionally authorizes the agent to stage the frozen
payload, submit and monitor only the package's bounded Slurm jobs, retrieve and
sanitize evidence, remove the exact agent-created remote run directory, and
commit or push the terminal record when the package directs it. Authoring
authority does not authorize an agent to automate MFA, expose credentials,
change administrator-owned modules or permissions, install remote software,
expand a frozen resource ceiling, access protected confirmation data, or
silently broaden the scientific claim. Those boundaries still require the
operator or system administrator.

## Control environment: `rmm`

The assumed control host is `rmm`, a Mac mini (`Macmini9,1`) with an Apple M1,
8 CPU cores, 16 GB memory, and `arm64`. The recorded operating system is macOS
26.5.2 build `25F84` with `/bin/zsh` as the operator shell.

`rmm` is used because it can reach the University of Idaho network through
the required VPN. It is an orchestration, authoring, validation, and staging
host; it is not a substitute for Lemhi's x86-64 CPU or GPU environment. Do not
compile Lemhi executables natively on Apple Silicon and assume they will run
on the cluster.

Recorded local tools include:

- Cargo and rustc 1.97.1 on `stable-aarch64-apple-darwin`;
- Git LFS 3.7.1; and
- GitHub CLI with credentials mediated by the macOS Keychain.

A restricted agent process may report that `gh` authentication is invalid
when it cannot read Keychain material even though `git push` succeeds through
the host credential helper. Treat `gh auth status` and Git HTTPS
authentication as separate checks. On macOS, prefer `shasum -a 256` unless
GNU `sha256sum` is known to be installed; Lemhi provides `sha256sum`.

Evidence created on other machines retains its recorded provenance. Do not
retroactively label older results as produced on `rmm` merely because `rmm`
commits or transfers them.

## Human SSH bootstrap

### Authentication boundary

Cold access requires both the University of Idaho VPN and human-supervised
authentication at the `login-ui` gateway. A public-key-only probe showed that
the gateway offered `keyboard-interactive` authentication; in practice this
means a password followed by Duo. The destination `lemhi` host accepted the
operator's RSA key after the gateway.

Therefore:

- the current noninteractive boundary is the gateway, not the destination;
- adjusting destination `authorized_keys` or home-directory permissions will
  not remove the gateway's MFA requirement;
- a root-owned, ACL-bearing Lemhi home directory is not by itself evidence of
  broken destination key authentication; and
- the public passwordless-RSA instructions may describe an older deployment,
  Open OnDemand, or destination-only authentication.

Never use `sshpass`, `expect`, stored passwords, recorded Duo passcodes, or an
agent prompt to automate the cold login.

### Required SSH aliases

The operator-local `~/.ssh/config` supplies two aliases:

- `login-ui` for `login-ui.c3plus3.org`; and
- `lemhi` for `lemhi.c3plus3.org`, with `ProxyJump login-ui`.

The observed configuration uses `ControlMaster auto`, `ControlPersist 28800`
(eight hours), `ServerAliveInterval 60`, `ServerAliveCountMax 3`, and TCP
keepalive for both aliases. Usernames, key paths, `ControlPath`, sockets, and
credentials are local state and must not be committed.

### Operator launch procedure

The operator performs these steps in an interactive terminal on `rmm`:

```sh
cd ~/src/cligen-rs

# 1. Connect the University of Idaho VPN and confirm it is active.

# 2. Bootstrap the gateway. Enter the password and approve Duo interactively.
ssh -MNf login-ui

# 3. Bootstrap Lemhi through the already authenticated gateway master.
ssh -MNf lemhi

# 4. Verify both control masters.
ssh -O check login-ui
ssh -O check lemhi

# 5. Prove that an agent-safe noninteractive command works.
ssh -o BatchMode=yes -o ConnectTimeout=10 lemhi 'hostname'
```

The expected control check contains `Master running`. If a check fails, the
operator repeats the supervised bootstrap; an agent must not fall back to an
interactive connection. A first connection may request host-key
confirmation. The operator must verify an unexpected or changed fingerprint
rather than automatically accepting it.

OpenSSH may warn that the connection is not using a post-quantum key exchange
algorithm. That is a server-capability/security warning, not an authentication
or Slurm failure. Do not weaken SSH verification to suppress it.

### Keepalive

After both masters are running, launch the repository keepalive in a dedicated
terminal on `rmm`:

```sh
cd ~/src/cligen-rs
research/a10/cluster/ssh-keepalive.sh --interval 300
```

The default interval is already 300 seconds. Equivalent forms are:

```sh
A10_SSH_KEEPALIVE_INTERVAL_SECONDS=300 \
  research/a10/cluster/ssh-keepalive.sh

research/a10/cluster/ssh-keepalive.sh --once
```

The script performs only `ssh -O check` for `login-ui` and `lemhi`. It cannot
create a cold connection or request credentials, and it exits if either
master disappears. VPN loss, host sleep, an eight-hour master expiry, gateway
restart, or network interruption can require another operator bootstrap.

To end a supervised session intentionally, stop the keepalive and close the
destination before the gateway:

```sh
ssh -O exit lemhi
ssh -O exit login-ui
```

## Agent transport rules

After the operator confirms bootstrap, every agent connection uses
noninteractive mode and a finite timeout:

```sh
ssh -o BatchMode=yes -o ConnectTimeout=10 lemhi '<remote command>'
scp -o BatchMode=yes local-file lemhi:relative/remote/path/
```

`sftp` and `rsync` may also use the configured `lemhi` alias. Agents must:

1. run `ssh -O check login-ui` and `ssh -O check lemhi` before a remote write;
2. fail closed and request human bootstrap if either master is absent;
3. keep remote commands bounded and quote remote variables with single quotes,
   for example `ssh ... lemhi 'squeue -h -u "$USER"'`;
4. stage into a unique relative run directory tied to the package and source
   commit;
5. compare local and remote source hashes before submission;
6. never SSH directly to a compute node outside a Slurm allocation; and
7. never retain usernames, absolute user paths, key material, control socket
   paths, passwords, Duo material, or unrestricted environment dumps in
   committed evidence.

## Transfer expectations from `rmm`

A10M2D2 measured a sustained warm-master SCP upload rate of 10.054 MiB/s and
download rate of 4.727 MiB/s across its registered cases. A 1,024-file tree
was 40.16 times slower to upload and 14.14 times slower to download than its
tar archive. Bundle small immutable objects before crossing the WAN.

The completion package's real uploads were consistent with that envelope:
the 214 MiB corpus archive averaged 7.052 MiB/s and the active 2.69 GiB
wheelhouse averaged 11.376 MiB/s. These are planning observations, not a
service guarantee. Routine single archives up to roughly 10 GiB are workable
in the observed window; roughly 50 GiB or larger should use resumable or
administrator-supported managed transport after a separate investigation.

SCP interruption can leave a partial object at its final requested name.
Always upload to `.part`, verify the remote byte count and SHA-256, and then
rename atomically. The installed `rsync` pair successfully resumed an
interrupted transfer; prefer it when restartability matters. Neither shared
Ceph free space nor an 8 GiB successful package proves the account quota, and
Globus availability remains unproved.

## Live Lemhi inventory established by A10M2

The following was observed, not inferred from the older GPU workshop:

| Surface | Observed state |
|---|---|
| Scheduler | Slurm 25.05.6 |
| Priority partition | `gpu-icrews`, allowed group `icrews`, priority tier 20, seven-day maximum |
| Fallback partition | `gpu-volatile`, priority tier 10, volatile/preemptible |
| Preemption | partition-priority with `CANCEL` semantics |
| `node03` | 4 × NVIDIA L40, 512 GB configured host memory, 64 configured CPUs/62 effective |
| `node04` | 4 × NVIDIA RTX A6000, 512 GB configured host memory |
| Successful L40 request | `--partition=gpu-icrews --gres=gpu:l40:1` routed to `node03` |
| Allocated L40 | 46,068 MiB reported, compute capability 8.9 |
| Driver/toolkit | driver 610.43.02; CUDA 12.8 V12.8.93 |
| Durable home | Ceph |
| Job temporary filesystem | `TMPDIR` observed as XFS |

I-CREWS membership provides priority access through `gpu-icrews`; it does not
make a job nonpreemptible or exempt it from scheduler policy. Use typed
`gpu:l40` GRES requests. An untyped `gpu:1` request can land on a different GPU
class, and `node04` is not an L40 node in the live configuration.

Compute nodes do not have internet access. Stage source, data, packages,
wheelhouses, model assets, licenses, and manifests before submission. The
completion package validated the specific offline framework contract below;
it did not validate arbitrary packages or candidate training.

## Current canonical A10 Python/L40 configuration

The current canonical configuration resolves through the immutable
[`lemhi-canonical-designation-index-v1`](../research/a10/lemhi_toolkit/configurations/lemhi-canonical-designation-index-v1.json)
to
[`lemhi-a10-py311-l40-v2-candidate`](../research/a10/lemhi_toolkit/configurations/lemhi-a10-py311-l40-v2-candidate.json),
semantic SHA-256
`5addee9c5db3592ee247eab2b5266ed5567fd9aaf24ed78dcb321ecbb001e22d`.
The `candidate` suffix is its immutable issuance identity; the later
designation index, not a mutation of that file, makes it current. The bound
smoke attestation SHA-256 is
`5caf106a84797b1d068be5693478f74b5368752bcfb78fa5eba186bdc21db350`.
Its governing policy is
[SPEC-LEMHI-CANONICAL-CONFIGURATION](specifications/SPEC-LEMHI-CANONICAL-CONFIGURATION.md).

This is the default for A10M3 and later single-L40 Python work:

- portable CPython 3.11.15, ABI `cp311`, from the exact pinned
  python-build-standalone artifact;
- NumPy 2.2.6 and PyTorch 2.7.1+cu128 from the exact 26-wheel, 3,865,978,880
  byte offline wheelhouse;
- `gpu-icrews` with typed `gpu:l40:1`, one GPU, and no requeue;
- final Ceph runtime and virtual-environment prefixes, with expansion and
  attempt state in marker-bound `toolkit_recoverable` job-local storage;
- `PYTHONPATH`, `PYTHONHOME`, and `LD_LIBRARY_PATH` cleared,
  `PYTHONNOUSERSITE=1`, and pip restricted to `--no-index --require-hashes`;
  and
- warm-MFA toolkit control, hash-promoted transfer, authenticated structured
  evidence, sanitized collection, and exact marked-root cleanup.

The accepted exact-asset smoke authenticated 27 compute and operational gates:
exact interpreter/ABI, standard library, subprocess and spawned
multiprocessing, compiled-extension linkage, NumPy arithmetic,
NumPy/PyTorch interop, CUDA visibility, exactly one L40,
tensor/autograd/checkpoint behavior, offline installation, environment
closure, toolchain/build closure, evidence, and exact cleanup.

Every consuming A10 package must record both the configuration ID and semantic
hash before submission. Do not silently resolve newer packages, use ambient
modules, move the environment, choose an untyped GPU, or fall back to Python
3.8. Any invalidation trigger in the canonical record requires a new
versioned candidate and a fresh bounded smoke before further commitments.

This canonical designation is scoped. It is not a performance, multi-GPU,
training-readiness, requeue, production-durability, A10M3-science, or
administrator-support claim.

## Optional single-node multi-L40 capability

A10M5O2 separately qualified the same canonical stack for explicit one-node
requests of two or four L40s. This is additive; the default remains
`gpu:l40:1`. Use the declarative `accelerator-l40-multigpu-v1` provider, set
`gpus` equal to the exact typed GRES count, and request only `gpu:l40:2` or
`gpu:l40:4` on `gpu-icrews`. Immediately before submitting, inspect all node03
allocations. Two GPUs require at least two idle L40s; four require node03 to
have no allocation. Never use this priority partition deliberately to
displace another job.

Live jobs `1014018`–`1014021` proved CPython 3.11.15, NumPy 2.2.6, PyTorch
2.7.1+cu128, CUDA 12.8, NCCL 2.26.2, one process per unique NVIDIA L40,
single-node collectives, DDP synchronization, checkpoint reload, expected
rank failure, exact accounting, and cleanup at one, two, and four GPUs. The
matrix consumed 650 actual GPU-seconds; its unused recovery reserve was
released.

Operational readiness does not imply speedup. In the frozen communication-
heavy microbenchmark, fixed-global throughput fell from 141,193 examples/s on
one GPU to 56,464 on two and 2,609 on four. Classify the current evidence as
`SINGLE-GPU-PREFERRED`. Request multiple GPUs only when a workload-specific
pilot shows that useful per-rank compute amortizes PCIe/NCCL/DDP communication.
This result says nothing about cross-node or heterogeneous operation.

## Legacy A10M2 offline framework and runtime contract

The login-visible Python 3.11.11 environment was not available on `node03`.
The compute node exposed Python 3.8.11 at
`/opt/modules/devel/python/3.8.11/bin/python3.8`. The successful immutable
wheel closure contained 23 fully hashed Linux x86-64 wheels and reconstructed
`torch==2.4.1+cu124` without network access. `pip check` passed. The observed
runtime was CUDA 12.4 with cuDNN 9.1 and NCCL 2.20.5, running under the
CUDA-12.8-capable 610.43.02 driver.

That exact Python 3.8 stack passed one-L40 tensor/autograd/optimizer/checkpoint/reload,
two-L40 NCCL all-reduce and one-step DDP, and a Slurm `USR1` checkpoint plus
manual resume/control-equivalence drill. It is a proved M2 capability stack
and now serves as an explicit legacy fallback only. It is not the default for
later milestones, and a failed or missing canonical asset must never select it
automatically.

Operational rules learned during reconstruction:

1. Build and verify the complete wheelhouse on `rmm`; transfer an archive as
   `.part`, verify its SHA-256 remotely, then promote it.
2. Install only with `--no-index --require-hashes` from that wheelhouse and
   run `pip check` before use.
3. Create a virtual environment at its final remote path. Moving it leaves
   entrypoint shebangs such as `torchrun` pointing at the old path.
4. Isolate `PYTHONPATH`, `PYTHONHOME`, user site packages, and ambient loader
   paths. Invoke distributed launch as `python -m torch.distributed.run`
   through the selected environment rather than a moved console script.
5. PyTorch emitted a NumPy initialization warning even after ambient-path
   isolation. NumPy is not in this frozen closure and no NumPy conversion was
   exercised. Any later NumPy use must add, hash, and test it explicitly.

The stage-2 storage check verified all 98 A10M1 objects on Ceph and XFS,
archive and many-object staging, a 64 MiB checkpoint-style copy-back, durable
fallback, and exact local cleanup. Because the mandatory Ceph hash pass
preceded timed copies, its rates describe a warm cache path only. Do not use
them as cold-I/O, data-loader, or training-throughput estimates. The copy-back
was verified after atomic rename but did not separately instrument `fsync`;
add explicit synchronization before making power-loss-durability claims.

## Known-good CUDA compiler contract

### Root cause discovered by A10M2D1

The login host is Intel Xeon Gold 6148 (Skylake) with AVX-512. `node03` is AMD
EPYC 7313 with AVX and AVX2 but without the tested AVX-512 feature groups. The
ambient login compiler is GCC 12.5 from a Spack prefix named
`linux-skylake_avx512`.

That ambient contract is invalid across the login-to-GPU-node boundary:

- the ambient GCC driver and preprocessing die with `SIGILL` on `node03`;
- CUDA compilation without an explicit `-ccbin` fails there;
- a login-built ambient binary also dies with `SIGILL` on `node03`; and
- that binary carries an RPATH to the architecture-targeted Spack
  `libstdc++` and `libgcc_s` runtime.

The exact faulting instruction or individual library was not captured, but the
CPU-feature, driver, preprocessing, RPATH, and controlled compiler outcomes
localize the operational cause to the architecture-targeted ambient
toolchain/runtime rather than the L40, CUDA driver, source, or GNU version
guard.

### Working configurations

The simplest observed compiler contract is direct CUDA 12.8 plus explicit OS
GCC 8.5:

```sh
/usr/local/cuda-12.8/bin/nvcc \
  -ccbin=/usr/bin/g++ \
  -O2 -std=c++17 \
  source.cu -o program
```

The advertised GCC 11.2 path also passed:

```sh
/usr/local/cuda-12.8/bin/nvcc \
  -ccbin=/opt/modules/devel/gcc/11.2.0/bin/g++ \
  -O2 -std=c++17 \
  source.cu -o program
```

Both compilers built the unchanged smoke on the login host and on `node03`.
All four resulting binaries saw one L40 and passed allocation, host-to-device
transfer, kernel execution, synchronization, device-to-host transfer,
checksum, and maximum-error checks. These are observed working configurations,
not a claim that the C3+3 administrator supports them for production.

Do not use `--allow-unsupported-compiler`, `-march=native`, or an implicit
ambient host compiler. Record the absolute CUDA and host-compiler paths in job
provenance.

## Minimal Slurm pattern

Use a committed batch script with explicit resources and compiler selection:

```bash
#!/bin/bash
#SBATCH --job-name=lemhi-cuda-smoke
#SBATCH --partition=gpu-icrews
#SBATCH --gres=gpu:l40:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
umask 077
ulimit -c 0

cuda_root=/usr/local/cuda-12.8
host_cxx=/usr/bin/g++
local_root=${SLURM_TMPDIR:-${TMPDIR:-/tmp}}
build_dir="${local_root%/}/lemhi-cuda-${SLURM_JOB_ID}"

test -x "$cuda_root/bin/nvcc"
test -x "$host_cxx"
cd "${SLURM_SUBMIT_DIR:?}"
mkdir -p "$build_dir"
trap 'rm -rf -- "$build_dir"' EXIT

nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
device_names=$(nvidia-smi --query-gpu=name --format=csv,noheader)
test "$(printf '%s\n' "$device_names" | wc -l)" -eq 1
printf '%s\n' "$device_names" | grep -qx 'NVIDIA L40'
"$cuda_root/bin/nvcc" -ccbin="$host_cxx" -O2 -std=c++17 \
  source.cu -o "$build_dir/program"
"$build_dir/program"
```

Add `#SBATCH --nodelist=node03` only when a frozen diagnostic requires that
specific host. The typed L40 GRES should otherwise supply the placement
constraint. Validate the allocated device count and type inside the job before
making GPU-result claims.

Slurm opens `--output` and `--error` paths before the script runs. Create the
relative log directory on Lemhi before submission:

```sh
mkdir -p logs
sbatch --parsable job.sbatch
```

The cleanup trap is safe only because `build_dir` is an agent-created,
job-specific child of a resolved temporary root. Never point recursive cleanup
at `$HOME`, `~`, an empty variable, the repository root, or a shared project
directory. Copy durable results and receipts back to the Ceph working directory
before job exit. `$SLURM_TMPDIR` was not guaranteed in A10M2; retain the
`TMPDIR`/`/tmp` fallback and record the actual filesystem.

## A10M4 operational hardening

A10M4 turned several plausible operational assumptions into observed failure
evidence. For new commitments, agents must use the revision-2 toolkit contract
rather than copying A10M4's corrective shell fragments.

### Validate closures, not visible components

Cargo without `rustc`, a compiler without its target standard library, and a
vendor directory at the wrong extracted depth are incomplete closures. Native
build packages must declare the toolchain provider and validate twice:

1. on `rmm`, inspect the archive, safe extraction layout, source/vendor
   relationship, target libraries, licenses, and offline metadata command; and
2. in the allocated compute preflight, validate exact executable paths and
   versions, loader resolution, compiler invocation, vendor root relative to
   source, and the registered bounded build smoke.

Never inherit the login host's architecture-targeted Spack compiler or treat
file presence as execution proof.

### Start jobs from a closed environment

Hardened Slurm submission uses `--export=NONE` or a provider-proved equivalent,
but Lemhi's site launch path may still supply Python or loader variables. Do
not make their mere presence a fatal entry guard. Record typed presence flags
without values, clear `PYTHONPATH`, `PYTHONHOME`, `LD_LIBRARY_PATH`, and other
prohibited ambient inputs, reconstruct only registered scheduler/device
variables and the plan's exact `PATH`, compiler, cache, temporary-directory,
and public operational values, then assert closure before the first Python
import. A variable that survives clearing or conflicts with the reconstructed
contract fails. Deterministic CUDA work sets
`CUBLAS_WORKSPACE_CONFIG=:4096:8` before Python or a CUDA framework is
imported. Evidence records the allowlisted contract, never `env` wholesale.

Plans also declare executable intent for job and supervisor assets. Preparation
rejects a required executable whose local mode is wrong, and remote
verification checks the mode in addition to byte count and SHA-256. If a
staged run must stop before submission, use the toolkit's `abort` lifecycle;
it validates the exact owner marker, removes only the registered durable root,
and proves absence without requiring a job-local receipt.

### Inspect allocation pressure, not presumed GPU activity

From the warm `lemhi` master, `sinfo -p gpu-icrews -N` reports node allocation
state and `squeue -p gpu-icrews` reports current jobs/users. `sacct` can review
recent partition history when its output is filtered on the `Partition` field.
These surfaces establish who owns Slurm allocations, CPU allocation counts,
and queue pressure; they do not establish live GPU utilization for an
unallocated node. During the 2026-07-10 through 2026-07-17 audit window, every
recorded `gpu-icrews` allocation belonged to `rogerlew.ui`, and both nodes were
idle with an empty queue immediately before the exact-asset smoke. Treat that
as a bounded observation, not a permanent exclusivity claim.

For an owned running job, `sstat -j <job>.batch` exposes CPU and memory step
telemetry. The toolkit records exact allocated GPU-seconds from Slurm
`ElapsedRaw` and an integer GPU-minute value rounded up for accounting. Neither
metric is a device duty-cycle or GPU-memory-utilization measurement.

### Measure export memory from a clean process lineage

Do not gate deployment memory with
`resource.getrusage(RUSAGE_SELF).ru_maxrss` inside a child forked by a
high-RSS trainer. Lemhi's Linux accounting retains the parent's historical
maximum across fork/exec. A10M5 consequently reported 3.09--3.13 GiB for an
export whose clean-process maximum is about 0.63 GiB. A direct control showed
an exec'd child with 8,876 KiB `/proc/self/status` `VmHWM` reporting 530,000
KiB `ru_maxrss` after launch from a 512 MiB parent.

For a CPU-export memory gate, finish and exit training first. Then have a
small shell or supervisor directly launch the export worker. Record the
worker's own `VmHWM` and `VmRSS` from `/proc/self/status`, and corroborate the
maximum with external `/usr/bin/time -v` whose launcher has not held the
training corpus or model state. Keep one-core affinity and all framework/BLAS
thread counts explicit. The A10M5R1 attribution measured 521--525 MB steady
RSS and 628--635 MB external maximum for eager and TorchScript variants.

This is an evidence correction, not permission to relax a memory threshold.
If a workflow cannot establish clean process lineage, treat peak RSS as
unavailable and stop the gate.

### Treat job-local state as toolkit-recoverable

The A10M4 failures left marked trees on persistent node-local `/tmp`; the
assumption that Slurm purged them was false. New work must declare
`toolkit_recoverable` storage. Primary admission checks the provider-declared
base, filesystem, owner, permissions, expanded bytes/inodes, outputs,
checkpoints, fixed margin, and free-space floor while holding a per-base claim.
It reserves a bounded recovery contingency before primary submission.

The toolkit supervisor owns the attempt process group, forwards catchable
signals, waits, atomically publishes status, cleans on every catchable exit,
and proves absence. Application or status-write failure never disables local
cleanup. `SIGKILL`, node loss, ambiguous scheduler state, or failed absence
proof yields `CLEANUP_INCOMPLETE` and retains the reserve.

Recovery is a separately registered Slurm role, never direct compute-node SSH.
It derives the exact node from authenticated terminal accounting, proves all
original jobs/steps/requeues absent and settled, then validates UID, marker,
ancestors, filesystem, and target twice before one bounded exact deletion. If
the node is unavailable or any identity differs, stop; never delete by user,
job name, prefix, wildcard, or process scan.

A10M4O2 live-accepted the controller commands for this path. After a terminal
`observe` authenticates `job_local_cleanup=false`, use only:

```text
recover --job-role <registered-role> --attempt-index <registered-index>
observe-recovery
```

The first command reconciles every authority-tagged scheduler ID before it
consumes the already reserved one-attempt contingency. The second requires
successful exact-node accounting, the original job ID, target-path hash, and
all registered recovery gates before collection or cleanup. A10M4O2's
controlled failure and recovery ran on `node03` in 2 and 1 elapsed seconds;
the marked target was absent afterward. This proves the mechanism, not future
node availability.

`observe` is not a blocking wait. Calling it while `squeue` still reports the
job returns `JOB_TERMINAL_MISMATCH` and leaves the attempt registered. Monitor
with `squeue`, wait for terminal `sacct` settlement, then invoke `observe`.
When recovery is not needed, the revision-2 evidence allowlist still requires
an honest `invoked=false` recovery receipt and clearly labeled non-invocation
stdout/stderr placeholders. Freeze those success-path artifacts before
execution; do not discover their absence at collection.

The same acceptance run proved the accounting interpretation with a 5-second
one-L40 job: `elapsed_seconds=5`, `actual_gpu_seconds=5`, and
`actual_gpu_minutes=1`. GPU minutes are rounded up per settled job for ledger
accounting, so three jobs totaling 8 GPU-seconds recorded 3 rounded minutes.

### Continue authority without resetting accounting

Do not hand-edit a new authority ID or choose a fresh state root when a source
correction needs a new run. Revision 2 gives each dispatch one exclusive
`initialize-authority`, canonical private ledger anchor, published head
checkpoints, and immutable authority revisions produced by `derive-run`.
Authority, package, budget, resource class/ceiling, branch, and push target do
not change. Every live reservation/submission reconciles the authority token
against Slurm accounting before spending.

Creating another revision-0 authority for the same package is not continuation.
It resets the ledger namespace and can violate a frozen attempt-count ceiling
even when cumulative elapsed GPU minutes remain modest. A10M5R3 exposed this
distinction while correcting two job-wrapper defects. Treat every settled job
across failed and successful run lineages as package resource use, and use
`derive-run` under the original budget for a prospective correction.

A local hash chain cannot detect restoration of both itself and its saved head
to an older valid prefix. Therefore missing or ambiguous external accounting
holds the authority; agents must not represent the local chain as rollback
proof.

### Separate raw collection from publication

Authenticated retrieval first creates a private `RAW_COLLECTED` receipt that
binds raw hashes, gates, and cleanup-authorizing markers. Publication then
performs typed, boundary-aware projection. Paths match only exact roots or
descendants, longest roots are replaced first, reserved token syntax and
invalid UTF-8 fail, and JSON is parsed and transformed structurally. Scientific
JSON may contain finite float metrics; duplicate keys, NaN, Infinity, and
non-finite overflow fail. Producers must use non-reserved notation such as
`[REMOTE_RUN_ROOT]` for any pre-projection diagnostic redaction. A final
forbidden-value scan still rejects unregistered leaks. Projection failure holds
publication but preserves exact cleanup authority and cannot alter gate
results. Retrying collection atomically retains the failed quarantine and
starts from a fresh authenticated download; it never overlays extracted files.

Typed replacement tokens are different from producer pre-redactions: use
reserved angle-bracket syntax such as `<REMOTE_RUN_ROOT>` in
`evidence_replacements`, and square brackets only in raw producer output.
A10M5R3 used the square-bracket form in a typed plan and consequently reached
`SANITIZATION_FAILED` after raw collection. Planning and amendment now validate
the token grammar prospectively so this defect stops before staging.

External `/usr/bin/time -v` writes the full timed command on its first line,
including durable and job-local paths. If that witness is allowlisted, register
typed path replacements in the prospective plan or have the producer emit a
non-reserved token such as `[REMOTE_RUN_ROOT]`. A10M5R2 confirmed that omitting
this rule holds collection even when every job gate passed.

### Transfer once only within a run lineage

Transfer receipts use integer nanoseconds and record `uploaded`, `resumed`, or
`already_verified`. A skip immediately revalidates the remote hash. SCP
partials are replaced or removed unless a provider proves range-safe resume.
Within one run lineage, immutable content-addressed assets may feed multiple
matrix jobs through an append-only manifest. This does not solve A10M4's
4.83-GB cross-run retransfers; cross-run caching remains deferred pending
quota, ownership, concurrency, garbage collection, and licensing policy.

### Application-owned preflight checklist

The toolkit authenticates declared gates but cannot infer scientific meaning.
An A10 package must additionally prove fully observed input windows under the
corpus missingness contract; checkpoint every cursor needed for the next
batch; deserialize checkpoints and CPU RNG state on CPU before explicit
relocation; and validate output completeness with a format-aware parser or a
byte-pinned fixture. Guessed line counts are not completeness evidence.

Package wrappers also own their staged directory topology and interpreter
order. Create nested parents before any shell redirection or Slurm log path
uses them; declaring `slurm/name.out` does not cause a staging tool to create
`slurm/`. On the compute node, construct and verify the canonical CPython 3.11
environment before running package selectors or resolvers. Do not call them
with the ambient Lemhi `python`, whose older syntax support can fail before an
otherwise valid allocation reaches training. These were separate A10M5R3
bootstrap defects: the first was caught before submission, while the second
settled one short failed allocation and required a new, prospectively pushed
run lineage.

## Submission and evidence lifecycle

An authorized agent should follow this sequence:

1. Confirm clean source state, package authority, resource ceiling, control
   masters, `icrews` eligibility, partition state, typed GRES, and current user
   jobs.
2. Freeze source hashes before any remote write.
3. Create one uniquely named remote run directory and stage only the frozen
   payload.
4. Verify remote hashes, then use `sbatch --parsable` and retain the job ID.
5. Monitor with `squeue`; obtain the final receipt with `sacct`, including
   state, exit code, elapsed time, time limit, CPUs, memory, GRES, and node.
6. Continue or stop according to the package's fail-closed gates. A Slurm exit
   code of zero is not proof that individual probes passed; retain an explicit
   status matrix and inspect each output.
7. Download logs and manifests, verify hashes locally, sanitize evidence, and
   classify observed fact separately from inference.
8. Remove only the exact remote run directory after verified retrieval, then
   confirm it is absent and no package job remains.
9. Run repository gates, close the package honestly, reconcile the roadmap and
   work-package catalog, and commit/push when the dispatch requires it.

Before submission, useful read-only checks include:

```sh
ssh -o BatchMode=yes -o ConnectTimeout=10 lemhi \
  'squeue -h -u "$USER"; sinfo -h -p gpu-icrews; sinfo -h -N -n node03 -o "%N|%t|%G"'
```

Quote the remote command as shown. Double-quoting the entire remote command on
`rmm` can expand local variables before SSH sends it.

## Error traps and interpretations

### `module load cuda/12.8` fails on the GPU node

The directory `/opt/modules/modulefiles` existed on `node03`, but
cache-bypassed Lmod discovery and loading still could not resolve
`cuda/12.8`. The same modulefile was visible on login and merely prepended
CUDA, TensorRT, and NCCL paths; it selected no host compiler.

For the validated smoke, use `/usr/local/cuda-12.8` directly. Do not assume
that `module use` proves a module can be loaded on a compute node.

### `gcc` dies by signal 4 or exit status 132

This is the known ambient AVX-512 compiler/runtime mismatch. Confirm the
resolved compiler path, `cc1`, RPATH, and loader dependencies. Select explicit
`/usr/bin/g++` or the tested GCC 11.2 path; do not work around it with compiler
version overrides or native-architecture flags.

### `nvcc fatal: Host compiler targets unsupported OS`

In A10M2 this line followed `gcc died due to signal 4` and was a secondary
diagnostic. CUDA 12.8's installed GNU guard accepted the tested GCC versions.
Read the preceding compiler failure before diagnosing an OS/version problem.

### A login-built binary still crashes

Compile-before-submit is viable only with a node-compatible compiler and
runtime. Inspect `readelf -d program` and `ldd program`. An RPATH into
`linux-skylake_avx512` is a red flag for `node03` even when compilation on
login succeeded.

### The shell prints `core dumped` despite `ulimit -c 0`

The message reports signal termination; it does not prove a core file was
written. Keep `ulimit -c 0`, inspect the run directory, and never retain core
files in evidence.

### Public documentation disagrees with live state

The older GPU workshop listed CUDA 12.2 and two L40s on each of `node03` and
`node04`. Live evidence showed CUDA 12.8, four L40s on `node03`, and four RTX
A6000s on `node04`. Another public page claimed the Lemhi login server matched
the compute-node processor generation, which is false for Intel login versus
AMD `node03`.

Treat published documentation as a hypothesis. Timestamp live `sinfo`,
`scontrol`, module, compiler, CPU, driver, and filesystem observations in each
new package.

### Collection rejects `<NO_OTHER_FAILURES>`

PyTorch `torchrun` can emit this reserved-looking placeholder in an expected
failure traceback. Toolkit projection revision 4 escapes raw third-party
angle tokens to `[[RAW_RESERVED_TOKEN:NAME]]`, records their counts, and then
applies authorized path/identity replacements. Do not delete, rewrite, or
exclude authentic failure evidence to make collection pass. If an older
projector fails closed after settlement, preserve raw evidence and use the
bounded projection-hardening successor; never resubmit the compute role.

### A job is accepted but the requested research claim is still unproved

A10M2/A10M2D1 proved transport, priority-partition access, typed L40
allocation, CUDA compilation, and the kernel smoke. The completion package
separately proved its frozen offline PyTorch stack, NCCL/DDP, signal handling,
and manual checkpoint/restart drill. It did not test Slurm requeue, candidate
training, scaling, cold storage performance, or production durability. Do not
promote a lower-level smoke result into any of those claims.

## Evidence sources

- [A10M2 package](work-packages/20260716-a10m2-lemhi-gpu-integration/package.md)
- [A10M2 live inventory](work-packages/20260716-a10m2-lemhi-gpu-integration/artifacts/inventory-live.md)
- [A10M2 CUDA failure](work-packages/20260716-a10m2-lemhi-gpu-integration/artifacts/j1-result.md)
- [A10M2D1 package](work-packages/20260716-a10m2d1-lemhi-cuda-drift-diagnostic/package.md)
- [A10M2D1 configuration matrix](work-packages/20260716-a10m2d1-lemhi-cuda-drift-diagnostic/artifacts/configuration-results.md)
- [A10M2D1 root cause](work-packages/20260716-a10m2d1-lemhi-cuda-drift-diagnostic/artifacts/root-cause.md)
- [A10M2D1 documentation drift](work-packages/20260716-a10m2d1-lemhi-cuda-drift-diagnostic/artifacts/documentation-drift.md)
- [A10M2D2 transfer characterization](work-packages/20260716-a10m2d2-rmm-lemhi-scp-characterization/package.md)
- [A10M2 completion package](work-packages/20260717-a10m2-completion/package.md)
- [A10M2 completion terminal](work-packages/20260717-a10m2-completion/artifacts/terminal.md)
- [A10M2 stage-2 result](work-packages/20260717-a10m2-completion/artifacts/stage2-result.md)
- [A10M5O1 multi-L40 toolkit hardening](work-packages/20260719-a10m5o1-multi-l40-toolkit-hardening/package.md)
- [A10M5O1R1 evidence projection hardening](work-packages/20260719-a10m5o1r1-evidence-token-projection-hardening/package.md)
- [A10M5O2 canonical multi-L40 qualification](work-packages/20260719-a10m5o2-canonical-multi-l40-qualification/package.md)
- [SSH keepalive implementation](../research/a10/cluster/ssh-keepalive.sh)
- [C3+3 GPU workshop](https://docs.c3plus3.org/docs/workshops/Cluster/GPU_Nodes.html)
- [C3+3 current partition guide](https://docs.c3plus3.org/docs/help/Tutorials/Partitions.html)
- [C3+3 Lemhi user guide](https://docs.c3plus3.org/docs/help/Getting_Started/)
