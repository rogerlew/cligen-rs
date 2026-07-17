# Cleanup receipt

Date: 2026-07-16 PDT

- All four J1 stdout/stderr files and both attempt source manifests were
  retrieved and locally hashed before cleanup.
- The exact package-scoped remote run contained 24 files.
- Wheelhouse files: 0.
- Runtime-environment files: 0.
- No checkpoint existed.
- No user Slurm job remained.
- The exact remote A10M2 run directory was removed and absence verified.

No broader home, cache, source, or scheduler object was targeted. Remote
scratch was job-scoped and the batch trap removed it when the amended job
exited.
