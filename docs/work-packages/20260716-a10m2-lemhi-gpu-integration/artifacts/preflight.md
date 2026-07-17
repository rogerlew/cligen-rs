# A10M2 Scaffold-Time Lemhi Preflight

Date: 2026-07-16
Evidence mode: Ran, read-only
Disposition: sufficient to scaffold; no Slurm job submitted

## Access boundary

- A host-context `ssh -o BatchMode=yes lemhi` command succeeded through the
  operator's existing MFA-bootstrapped control masters.
- The gateway offered only `keyboard-interactive` during a fresh public-key-
  only probe; Lemhi accepted the configured RSA key through the gateway.
- The operator control host requires University of Idaho VPN connectivity.

No credential, username, socket path, home path, or key material is retained
here.

## Live scheduler and authorization inventory

- Lemhi reports Slurm 25.05.6.
- The active account is a member of the `icrews` group.
- `gpu-icrews` is `UP`, allows group `icrews`, contains `node03` and `node04`,
  has priority tier 20, and a seven-day maximum.
- `gpu-volatile` is `UP`, allows group `hpc`, contains `node01`--`node05`, has
  priority tier 10, and carries QOS `volatile`.
- Slurm reports `PreemptType=preempt/partition_prio` and
  `PreemptMode=CANCEL`; the package will not deliberately test displacement.
- No user job was present during the preflight.

This proves visibility and configured eligibility, not allocation. A bounded
`sbatch` execution is required to establish actual GPU authorization.

## Live GPU inventory

| Partition-visible node | Live GRES | State during preflight |
|---|---|---|
| `node03` | `gpu:l40:4` | idle |
| `node04` | `gpu:rtxa6000:4` | idle |

`node03` reported 512000 MB configured memory, 64 configured CPUs, 62
effective CPUs, Linux 4.18.0-553.137.1.el8_10, and Slurmd 25.05.6. A10M2 uses
typed `gpu:l40` requests and does not infer L40 placement from the partition
name alone.

## Live software and storage inventory

- The default system Python is 3.6.8.
- After `module use /opt/modules/modulefiles`, the live alternate tree exposes
  CUDA 12.8 and Python 3.8.11/3.11.11.
- The public guide's CUDA 12.2 example is not present in that live tree.
- `nvidia-smi` is installed on the login host; driver/GPU usability remains a
  compute-allocation measurement.
- The live home filesystem is Ceph. Project/quota/local-scratch behavior is
  not yet established and must be measured by A10M2.

## Scaffold conclusion

The read-only evidence supports a bounded `gpu-icrews` integration package.
It does not yet support claims that `sbatch`, CUDA kernels, offline PyTorch,
NCCL/DDP, node-local staging, signals, checkpoint resume, requeue, or cleanup
work for A10.
