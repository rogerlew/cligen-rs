# Amendment 01 — C1 preamble localization

Date: 2026-07-17 PDT
Applied after C1-01 and before P0

## Evidence

C1-01 (`1013668`) received one typed L40 on `node03` but exited `1:0` after
one second with empty stdout/stderr and 4,908 KiB batch MaxRSS. Its script emits
the first output only after three executable checks and job-local setup. No
CUDA compile, framework install, corpus extraction, storage measurement, or
scientific check ran. The live login probe cannot distinguish those
compute-node preconditions because A10M2D1 already proved login/compute path
drift.

## Prospective correction

Add P0, a five-minute-ceiling one-L40 diagnostic on `node03`, to report only:

- the three frozen executable checks and bounded Python candidates;
- system Python identity;
- job-local root availability and collision status; and
- the allocated GPU identity.

P0 changes no C1 source or pass rule and does not install an environment or
touch corpus data. A functional C1 correction, if supported, must be frozen and
published in a second amendment before resubmission.

Conservative requested accounting for C1-01, P0, a corrected C1, C2, C3a, and
C3b is 55 GPU-minutes. The hard 60-GPU-minute package ceiling remains intact.
