# Prospective amendment 006 — one-core RSS execution

## Trigger

Lineage R6 job `1013875` used the bounded 365-day export protocol and passed
all gates except the unchanged absolute safeguard. The isolated export still
reported 3,319,341,056 peak RSS; benchmark dispersion passed and its worst
runtime ratio was `3.7523300241` (`PASS`).

The isolated RSS process still differed from the normative benchmark in one
material respect: it inherited the eight-CPU Slurm allocation and relied only
on `OMP_NUM_THREADS=1`. The freeze requires one pinned CPU core. PyTorch also
has separate intra-operation and inter-operation pools, and linked BLAS
runtimes accept their own thread controls. Leaving those implicit can create
thread stacks and backend workspaces that are absent from the frozen one-core
execution surface.

## Prospective correction

Before importing PyTorch, the next lineage pins the RSS subprocess to the
first CPU in its allocated affinity mask. Before loading or invoking the
export, it sets PyTorch intra-operation and inter-operation threads to one.
The subprocess environment also fixes OpenMP, MKL, and OpenBLAS threads to
one. The same export, inputs, 365-day state-carrying chunks, 100-year horizon,
RSS API, and 2 GiB threshold remain unchanged.

## Stop rule

This is the last RSS measurement-conformance correction. If the explicitly
one-core, bounded-memory export remains above 2 GiB, A10M5 records the
architectural safeguard failure rather than relaxing the threshold or
continuing measurement amendments.

R6 remains a failed diagnostic attempt and cannot promote.
