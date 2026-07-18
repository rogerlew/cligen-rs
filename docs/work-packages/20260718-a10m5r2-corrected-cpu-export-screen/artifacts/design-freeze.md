# A10M5R2 prospective correction freeze

The only correction relative to A10M5 is process lineage for CPU memory
measurement. The trainer writes and closes the export, then exits. The job
shell directly execs a separate one-core inference worker under external
`/usr/bin/time -v`; the worker reports `/proc/self/status` `VmHWM` and
`VmRSS`. Those two independent fresh-address-space values gate 2 GiB.

The twelve architecture/pooling/tail configurations, seed, corpus roles,
training schedule, identities, benchmark stations and horizons, timing
protocol, promotion rule, and every numerical threshold remain frozen at
A10M5. No protected role is opened.

## Implementation completion

The exact A10M5 `screen.py` is staged byte-for-byte as `screen_core.py` and
imported by a small trainer entry point. The trainer performs the frozen fit,
checkpoint, model-record, and TorchScript export operations, writes the export
metadata, and returns. The job shell writes `trainer-exited.marker` only after
that process exits.

The same small shell then directly launches a new Python process with the GPU
hidden, one pinned core, and one PyTorch/OpenMP/MKL/OpenBLAS/NumExpr thread.
That worker loads the persisted TorchScript export, generates and benchmarks
the unchanged nested streams, compares all twelve hashes with the immutable
A10M5 predecessor row, and records its own `/proc/self/status` `VmRSS` and
`VmHWM`. `/usr/bin/time -v` measures the whole worker from outside. A separate
non-Torch finalizer joins trainer and worker evidence only after the worker
exits.

All twelve predecessor benchmark manifests and validation values are copied
from committed A10M5 evidence into a single hash-bound staged manifest. Exact
stream and fit identities are gates. Each configuration has one attempt,
requests one L40, eight CPUs, 65,536 MiB, and 30 minutes, and runs sequentially
on node03. The run reserves one five-minute exact-node recovery allocation.
