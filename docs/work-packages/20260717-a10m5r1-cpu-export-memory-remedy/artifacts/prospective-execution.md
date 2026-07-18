# A10M5R1 prospective execution record

The first allocation uses one L40 only because canonical Lemhi measurements
belong in the established typed Slurm environment. The GPU is hidden from all
workers. Each worker is a fresh process pinned to one CPU with one PyTorch,
OpenMP, MKL, OpenBLAS, and NumExpr thread.

The synthetic reference is the smallest A10M5 streaming architecture
(`N0-l32-w128-d2`): two 128-wide encoder layers, a 32-state GRU, and a
15-value head. Seed 147031 initializes an eager reference and a strict traced
export. Deterministic synthetic features cover 36,525 days and are processed
in 365-day chunks with exact hidden-state carry.

Fresh workers test import-only, load-only, eager, default TorchScript,
TorchScript with optimized execution disabled, MKLDNN disabled, and a frozen
TorchScript module. Every inference variant hashes the complete float32 output
stream and must match the eager reference exactly before it can be a remedy.
Phase snapshots record `ru_maxrss`, `/proc/self/status`,
`/proc/self/smaps_rollup`, categorized `/proc/self/smaps` RSS, thread and stack
state, model/input tensor bytes, retained output bytes, and `/usr/bin/time -v`.

The allocation is diagnostic-successful when all variants and cleanup
complete, even if none meets 2 GiB. A second allocation is authorized only if
the first identifies an exact output-preserving candidate at or below 2 GiB;
it will exercise that one recipe against a candidate-fit export and the frozen
runtime contract. Otherwise this package stops before approximation,
dependency expansion, threshold change, or model-family change.
