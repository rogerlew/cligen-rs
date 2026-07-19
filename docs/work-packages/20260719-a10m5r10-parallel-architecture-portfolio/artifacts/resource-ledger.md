# Resource ledger

| Item | Requested | Actual | Disposition |
|---|---:|---:|---|
| Control materialization, job 1014028 | 30 GPU-min | 885 s / 15 charged min | settled, PASS |
| Eight bootstrap-failed candidate roles, jobs 1014031–1014038 | 720 GPU-min | 1,092 s / 24 charged min | settled, FAIL |
| Physics K1, job 1014039 | 90 GPU-min | 1,836 s / 31 charged min | settled, PASS |
| Physics K2, job 1014040 | 90 GPU-min | 1,970 s / 33 charged min | settled, PASS |
| Exact-node cleanup contingency | 5 GPU-min | 0 | released after verified cleanup |

Authority ceiling: 935 GPU-minutes. Eleven primary attempts were submitted,
one for every registered role. Actual settled use was 103 GPU-minutes. No
retry or recovery job was invoked. Every supervised job-local target and the
exact durable remote root were verified absent before terminal close.
