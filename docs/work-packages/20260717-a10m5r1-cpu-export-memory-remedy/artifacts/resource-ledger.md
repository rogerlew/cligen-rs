# A10M5R1 resource ledger

| Run/job | Requested GPU-min | Actual GPU-sec | Outcome |
|---|---:|---:|---|
| R1 / 1013928 | 30 | 99 | measurements complete; invalid toolkit gate shape |
| R2 attribution / 1013929 | 30 | 101 | source enumeration failure |
| R2 acceptance / 1013930 | 30 | 165 | stale launcher filename, pre-fit failure |
| R4 acceptance / 1013931 | 30 | 520 | completed and toolkit-valid |
| **Total** | **120** | **885** | four-allocation ceiling exhausted |

R3 was prepared and aborted before staging or submission. No recovery job was
invoked. Ceiling-rounded scheduler accounting is 16 GPU-minutes; elapsed
device allocation is 14.75 GPU-minutes. The package's five-minute recovery
reserve was not consumed.

All four durable run roots are absent. Every submitted job reported job-local
cleanup true. R4 collected, sanitized, cleaned, and reached
`LEMHI-TOOLKIT-RUN-CLOSED`. R1 evidence is retained under `raw-r1/`. R2's
unsanitized evidence remains only in restricted controller quarantine; its
exact remote root was manually authenticated and removed after the authoring
defects prevented toolkit closure.
