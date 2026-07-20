# Execution gates

| Gate | Result |
|---|---|
| Published source `bbb3075` equals execution source | PASS |
| Control and calendar/missingness preflight | PASS |
| Exact four-role admission matrix | PASS |
| Candidate A complete evidence | FAIL — parameter-count interface |
| Candidate B complete evidence | FAIL — parameter-count interface |
| Candidate C environment setup | FAIL — job-local ENOSPC |
| Candidate D submission | NOT EXECUTED — upstream failure |
| Matched four-arm selector replay | NOT EXECUTED — incomplete portfolio |
| Partial evidence collection | PASS — 70 present, 19 explicitly absent |
| Exact remote and job-local cleanup | PASS |
| Toolkit terminal | PASS — `LEMHI-TOOLKIT-RUN-CLOSED` |

The jobs charged 19 + 31 + 36 + 2 = 88 GPU-minutes against the 995-minute
ceiling. The five-minute recovery reserve was released unused.

No production function under `crates/` changed, so coverage/CRAP gates do not
apply.
