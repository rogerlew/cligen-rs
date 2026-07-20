# Execution gates

| Gate | Result |
| --- | --- |
| Published R13R1 source `927c6147` | PASS |
| Calendar and missingness preflight before allocation | PASS |
| Control admission and job `1016150` | PASS, 20 GPU-min |
| Flexible-hierarchy admission and job `1016152` | PASS, 84 GPU-min |
| Shared-slow admission and job `1016153` | PASS, 81 GPU-min |
| Candidate concurrency after serialized bootstrap | PASS |
| One attempt per role; no scientific retry | PASS |
| All registered candidate and control gates | PASS |
| Evidence allowlist and sanitized collection | PASS, 51 / 51 |
| Semantic plan authentication via R13R2 | PASS |
| Replay pass A/B byte identity | PASS |
| Protected roles | PASS, sealed |
| Temporal eligibility | FAIL, both candidates |
| Marker-bound remote cleanup | PASS, absent |
| Job-local cleanup | PASS, verified absent |
| Recovery reservation | PASS, released unused |
| Toolkit terminal | PASS, `LEMHI-TOOLKIT-RUN-CLOSED` |
| Charged authority usage | PASS, 185 / 515 GPU-min |
| Full package freeze verifier | PASS |
| Toolkit tests | PASS, 84 / 84 |
| Cargo format, Clippy, and tests | PASS |

The temporal eligibility failure is a scientific result. The intermediate
R13R1 replay failure was an operational authentication defect closed by the
zero-GPU R13R2 successor before cleanup.
