# A10M5R1 R2 acceptance disposition

R2 Slurm job 1013930 failed after 165 seconds because the copied launcher
retained A10M5's `screen.py` filename instead of invoking the frozen A10M5R1
`accept.py`. The error occurred after offline environment creation and the
faithful Rust build but before any candidate fit. The supervisor proved
job-local cleanup; toolkit observation recorded a failed role with 3 actual
GPU-minutes and no scientific inference.

The filename is corrected prospectively. The package's fourth and final
allocation is reserved for this decisive candidate-fit acceptance rather than
the optional deterministic/nondeterministic attribution contrast. R1 already
demonstrated an exact deterministic recipe below 2 GiB on synthetic state;
only candidate-fit acceptance can establish the package terminal.
