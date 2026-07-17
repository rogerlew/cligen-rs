# C3+3 Lemhi GPU computing for agents

This is the operational runbook for agent-driven Lemhi GPU work from `rmm`.
It consolidates the live evidence from A10M2, A10M2D1, and the CPython 3.11
toolkit smoke. Live cluster state was observed on 2026-07-16 and 2026-07-17
and must be rechecked before each new resource commitment; public C3+3
documentation has demonstrably drifted.

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

The current canonical configuration is
[`lemhi-a10-py311-l40-v1`](../research/a10/lemhi_toolkit/configurations/lemhi-a10-py311-l40-v1.json),
semantic SHA-256
`0b1115a6801259c62d9550c877a3c49a897319348ba1c2027be0d9c4f77c1179`.
Its governing policy is
[SPEC-LEMHI-CANONICAL-CONFIGURATION](specifications/SPEC-LEMHI-CANONICAL-CONFIGURATION.md).

This is the default for A10M3 and later single-L40 Python work:

- portable CPython 3.11.15, ABI `cp311`, from the exact pinned
  python-build-standalone artifact;
- NumPy 2.2.6 and PyTorch 2.7.1+cu128 from the exact 26-wheel, 3,865,978,880
  byte offline wheelhouse;
- `gpu-icrews` with typed `gpu:l40:1`, one GPU, and no requeue;
- final Ceph runtime and virtual-environment prefixes, with wheel expansion in
  scheduler-purged job-local storage;
- `PYTHONPATH`, `PYTHONHOME`, and `LD_LIBRARY_PATH` cleared,
  `PYTHONNOUSERSITE=1`, and pip restricted to `--no-index --require-hashes`;
  and
- warm-MFA toolkit control, hash-promoted transfer, authenticated structured
  evidence, sanitized collection, and exact marked-root cleanup.

The accepted smoke authenticated 19 gates: exact interpreter/ABI, standard
library, subprocess and spawned multiprocessing, compiled-extension linkage,
NumPy arithmetic, NumPy/PyTorch interop, CUDA visibility, exactly one L40,
tensor/autograd/checkpoint behavior, offline installation, and cleanup.

Every consuming A10 package must record both the configuration ID and semantic
hash before submission. Do not silently resolve newer packages, use ambient
modules, move the environment, choose an untyped GPU, or fall back to Python
3.8. Any invalidation trigger in the canonical record requires a new
versioned candidate and a fresh bounded smoke before further commitments.

This canonical designation is scoped. It is not a performance, multi-GPU,
training-readiness, requeue, production-durability, A10M3-science, or
administrator-support claim.

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
- [SSH keepalive implementation](../research/a10/cluster/ssh-keepalive.sh)
- [C3+3 GPU workshop](https://docs.c3plus3.org/docs/workshops/Cluster/GPU_Nodes.html)
- [C3+3 current partition guide](https://docs.c3plus3.org/docs/help/Tutorials/Partitions.html)
- [C3+3 Lemhi user guide](https://docs.c3plus3.org/docs/help/Getting_Started/)
