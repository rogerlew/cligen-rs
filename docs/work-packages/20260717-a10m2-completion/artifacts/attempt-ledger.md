# Attempt ledger

| Attempt | Job ID | State | Requested | Classification |
|---|---:|---|---:|---|
| C1-01 | 1013668 | `FAILED`, `1:0`, 1 s | 15 GPU-min | preamble failure before first output; no scientific gate reached |
| P0-01 | 1013670 | `COMPLETED`, `0:0`, 0 s | 5 GPU-min | Python 3.11 absent; Python 3.8.11, CUDA, compiler, local root, and L40 valid |
| C1-02 | 1013671 | `COMPLETED`, `0:0`, 76 s | 15 GPU-min | corrected CUDA, offline framework, one GPU, stage 2, fallback, and cleanup passed |
| C2-01 | 1013672 | `FAILED`, `126:0`, 1 s | 10 GPU-min | two L40s visible; stale moved-venv `torchrun` shebang failed before import |

C1-01 allocated `node03` and one typed L40. Empty logs plus 4,908 KiB batch
MaxRSS localize the failure to the frozen executable/job-local preconditions.
Amendment 01 authorizes bounded P0 before any functional retry.

P0 localized the failed precondition to the login-only Python 3.11 path.
Amendment 02 freezes the compute-valid Python 3.8 / PyTorch CUDA 12.4 lock and
source compatibility changes before C1-02.

C1-02 passed. Its non-gating ambient NumPy probe warning motivated Amendment
03 isolation for the still-unsubmitted C2/C3 jobs; it changes no C1 result.

C2-01 proved allocation/device visibility but reached no collective. Amendment
04 freezes interpreter-module invocation and shorter still-unrun limits so a
complete ladder remains within 53 requested GPU-minutes.
