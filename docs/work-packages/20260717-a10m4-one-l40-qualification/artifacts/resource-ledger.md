# A10M4 resource ledger

Package ceiling: 2,400 requested L40 GPU-minutes (40 GPU-hours).

| Resource class | Count | Requested GPU-minutes | Elapsed seconds |
|---|---:|---:|---:|
| Allocated qualification attempts | 10 | 1,200 | 2,907 |
| Exact job-local recovery | 1 | 5 | 10 |
| Staged-only administrative abort | 1 | 0 | 0 |
| **Total** | **12 records** | **1,205** | **2,917** |

Requested use was 50.21% of the package ceiling, leaving 1,195 requested
GPU-minutes unused. Because Lemhi accounting did not emit a GPU TRES for these
typed-GRES jobs, elapsed GPU use is conservatively derived from each job's
single-L40 request and `ElapsedRaw`: 2,917 seconds, or 48.62 GPU-minutes
(0.8103 GPU-hours). The request plans and job receipts independently prove one
typed L40 per qualification allocation.

Run 11 resource evidence records 5.6462 seconds for the qualification training
work, 71,663,616 peak GPU bytes, 426.8666 seconds for resume/generation/
benchmark, 477,437,952 CPU peak RSS bytes, 148,482 export bytes, and a 1.3538-
second cold start. Its two-step projection of 0.01882 GPU-hours for 12 such
qualification configurations is diagnostic only and is not a full-training
M5 cost estimate.
