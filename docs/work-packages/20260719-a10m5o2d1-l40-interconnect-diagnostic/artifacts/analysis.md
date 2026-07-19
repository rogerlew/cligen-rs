# A10M5O2D1 analysis

## Answer

The A10M5O2 four-GPU slowdown is not caused by an external network hop. It is
an intra-node NCCL transport-selection failure or limitation: NCCL 2.26.2 uses
direct CUDA peer transfers for every two-GPU group, but declines peer-to-peer
transport when all four node03 L40s participate and routes the collective
through host shared memory.

## Physical topology and peer capability

`nvidia-smi topo -m` reported all GPU-to-GPU relations as `NODE`: PCIe paths
that traverse host bridges within a NUMA node, not NVLink. GPUs 0–1 were
reported in NUMA domain 0 and GPUs 2–3 in NUMA domain 1. The PCI bus IDs were
01:00.0, 25:00.0, C1:00.0, and E1:00.0. Both the driver read and write P2P
matrices marked every off-diagonal relation `OK`; PyTorch independently
reported that every device could access every peer.

The hardware therefore exposes peer access across all six pairs. The observed
pair bandwidth nonetheless has two classes. At 128 MiB, pairs 0–1 and 2–3
reached approximately 20.1 GB/s, while 0–2, 0–3, 1–2, and 1–3 reached
14.5–14.6 GB/s. This is consistent with two favored local PCIe/host-bridge
pairings and four less favorable paths.

## Transport evidence

For every two-rank default, NCCL logged `intraNodeP2pSupport 1` and channel
connections `via P2P/CUMEM`. Disabling P2P changed those channels to
`SHM/direct/direct` and reduced 128 MiB bus bandwidth:

| Group | Default GB/s | P2P disabled GB/s | Default/control ratio |
|---|---:|---:|---:|
| 0–1 | 20.117 | 5.383 | 3.74× |
| 0–2 | 14.488 | 1.037 | 13.97× |
| 0–3 | 14.619 | 1.067 | 13.70× |
| 1–2 | 14.597 | 1.025 | 14.24× |
| 1–3 | 14.503 | 1.119 | 12.96× |
| 2–3 | 20.067 | 4.936 | 4.07× |

The four-rank default instead logged `intraNodeP2pSupport 0`; every ring edge
used `SHM/direct/direct`. At 128 MiB it produced 1.148 GB/s bus bandwidth and
1.754 seconds for ten all-reduces. The explicit `NCCL_P2P_DISABLE=1` control
produced 1.155 GB/s and 1.744 seconds. Its slight 0.6% apparent advantage is
noise, not a material difference. The same equivalence appears at 1 and 16
MiB.

NCCL also discovered and initialized the node's `mlx5` InfiniBand interfaces,
and reported GPU Direct RDMA disabled. That initialization does not establish
that the collective crossed the network. The per-channel ring evidence names
shared memory for all four-rank edges, so host-memory staging is the actual
same-node data path measured here.

## Disposition and remaining uncertainty

The diagnostic distinguishes the mechanism but does not establish why NCCL
sets four-rank `intraNodeP2pSupport` to zero. Plausible areas for a future,
separately bounded investigation include NCCL's topology policy for the full
PCIe graph, CUDA CUMEM behavior, ACS/IOMMU configuration, and the asymmetric
CPU-affinity/NUMA presentation for GPUs 2–3. None is promoted as the cause.

Do not infer four-GPU performance from pairwise `nvidia-smi` P2P status. For
any intended rank count, inspect NCCL's actual channel transport at that rank
count. Keep one L40 as the canonical default. Two-L40 work remains an optional
workload-specific choice; pairs 0–1 and 2–3 are fastest when explicitly
available, but ordinary two-GPU Slurm allocations must not assume an
unadvertised physical pair. Hold four-L40 performance use until a supported
remedy is proved. Do not set undocumented NCCL environment overrides as a
global toolkit default.
