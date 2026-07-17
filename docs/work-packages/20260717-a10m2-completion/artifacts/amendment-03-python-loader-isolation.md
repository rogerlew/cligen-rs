# Amendment 03 — Python and loader isolation

Date: 2026-07-17 PDT
Applied after C1-02 and before C2

C1-02 passed every frozen gate, including `pip check` and the framework smoke,
but PyTorch emitted a non-gating warning while probing an ambient NumPy path.
The locked environment does not declare NumPy and the smoke performs no
NumPy conversion. The warning does not invalidate C1, but inherited Python or
loader paths are unnecessary and D1 already proved ambient architecture paths
can be unsafe on `node03`.

Prospectively for unsubmitted C2/C3 only:

- unset `PYTHONPATH` and `PYTHONHOME`;
- set `PYTHONNOUSERSITE=1`; and
- replace inherited `LD_LIBRARY_PATH` with only the selected Python root
  library directory. PyTorch's hashed wheel stack retains its own relative
  runtime library search paths.

No framework version, test, pass rule, or resource changes. C1-02 remains
bound to the published Amendment 02 source at commit `09208f4`.
