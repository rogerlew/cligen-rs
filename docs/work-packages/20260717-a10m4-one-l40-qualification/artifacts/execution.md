# A10M4 execution record

Execution used the warm MFA-bootstrap SSH control path from `rmm`, toolkit
authority `a10m4-qualification-r1-authority`, and exact run-local remote roots.
Every compute allocation requested `gpu-icrews`, `gpu:l40:1`, 8 CPUs, 65,536
MiB, and a 120-minute limit except the explicit five-minute cleanup recovery.

| Run | Source | Slurm | Elapsed | Result and disposition |
|---|---|---:|---:|---|
| r1 | `dfcc523` | 1013761 | 105 s | Failed: standalone Cargo lacked `rustc`; collected, cleaned, closed. |
| r2 | `c6446c2` | none | 0 s | Staged only under a mistaken new authority identity; submission failed closed, exact marker cleanup passed, zero allocation. |
| r3 | `c6446c2` | 1013766 | 122 s | Failed: vendored Cargo path was one directory too high; collected, cleaned, closed. |
| r4 | `cf17353` | 1013769 | 189 s | Failed: deterministic CuBLAS workspace environment absent; old traceback exposed the forbidden remote prefix, so identities were recorded and marker cleanup was performed. |
| r5 | `8d87f71` | 1013770 | 24 s | Failed: stale job-local directories exhausted node03 `/tmp`; receipt creation could not complete. |
| recovery | n/a | 1013771 | 10 s | Removed only four named stale A10M4 job-local roots and verified their absence. |
| r6 | `cad91ec` | 1013772 | 190 s | Failed: A10M1's intentional null leap-day row entered the training window; identities recorded and marker cleanup passed. |
| r7 | `9d21665` | 1013773 | 201 s | Finite update passed; fresh restart used an unpropagated window cursor; collected, cleaned, closed. |
| r8 | `f7984cb` | 1013774 | 196 s | Restart loaded the CPU RNG ByteTensor onto CUDA; collected, cleaned, closed. |
| r9 | `be94000` | 1013775 | 618 s | Sixteen gates passed; faithful completeness missed the trailing footer; collected, cleaned, closed. |
| r10 | `d225056` | 1013776 | 634 s | Sixteen gates passed; the 365-day hypothesis was falsified; collected, cleaned, closed. |
| r11 | `1b791b9` | 1013777 | 628 s | `COMPLETED (0:0)`; all 20 gates passed; collected, cleaned, closed. |

The prospective amendment record is `amendment-001.md` through
`amendment-010.md`. Runs 4--6 predated the final sanitization/cleanup behavior;
their manual recovery is retained rather than represented as a normal toolkit
close. All toolkit-publication material that exists for every run is copied
under `toolkit/run-N/`.

Run 11 used plan ID
`e529321c329ea57192a3bcd1e689ad594f929c51605256dfbd909e39bf21b090`.
Its 4,833,468,177-byte asset set was staged through `.part`, verified by byte
count and SHA-256, and promoted before job submission. The successful evidence
archive is 40,960 bytes with SHA-256
`f79b3f3343936b9f4405b42ddefd07bf46b01eeec116ddee9672a17af57be63f`.
The exact remote-root cleanup receipt reports `remote_absent: true`, and the
terminal receipt is `LEMHI-TOOLKIT-RUN-CLOSED`.

No development or confirmation target series was read. The two optimizer
updates existed only to qualify restart behavior, and no fitted checkpoint or
export was retained outside sanitized evidence.
