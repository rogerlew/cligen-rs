# A10M5R3 resource and lifecycle ledger

| Lineage | Source | Settled jobs | Passed | Failed | GPU-seconds | Rounded GPU-minutes | Terminal |
|---|---|---:|---:|---:|---:|---:|---|
| r1 | `ce79430` | 0 | 0 | 0 | 0 | 0 | aborted before submission |
| r2 | `4773cc5` | 1 | 0 | 1 | 274 | 5 | receipt promotion failure |
| r3 | `22d50a9` | 10 | 9 | 1 | 2,422 | 46 | ambient Python resolver failure |
| r4 | `47963a9` | 18 | 18 | 0 | 7,722 | 137 | jobs passed; publication sanitization failed |
| **Total** | | **29** | **27** | **2** | **10,418** | **188** | resource-count hold |

The 545-minute ceiling was not exhausted, and the five-minute recovery role
was never invoked. The package nevertheless authorized at most 18 primary
jobs. Creating fresh authorities and budget IDs for r2--r4 did not reset the
package-level attempt count; 29 settled jobs is a hard governance failure.

All 18 r4 jobs authenticated job-local cleanup. Raw collection bound 239 files
to their hashes and owner marker before projection failed. A10M5R3R1 replayed
projection v3 with the grammar-correct token, then committed `clean.sh` hash
`3d06f34f23e46ff7ca89948216cfccf53fe1a3d5a7ef1229541f579f22edf77f`
revalidated owner marker
`d43dedb292ea34af76867b96df27499dd9e068586ec7a43bb75ae3f5560f458b`
twice and removed only `runs/a10m5r3-screen-r4`. A separate absence probe
returned `REMOTE_ABSENT`. The parent toolkit is intentionally not labeled
closed.
