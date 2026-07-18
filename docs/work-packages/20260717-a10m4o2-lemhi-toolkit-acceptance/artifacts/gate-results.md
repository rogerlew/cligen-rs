# A10M4O2 gate results

| Gate | Result | Evidence |
|---|---|---|
| Live pre-submission abort | PASS | `live/abort.json`; no allocation |
| Local executable-mode rejection | PASS | `fixture-results/executable-mode-rejection.json` |
| L40 success | PASS | job `1013867`, 5 seconds, all three gates |
| Seconds/minutes accounting | PASS | 5 seconds → 5 GPU-seconds → 1 rounded minute |
| Authenticated controlled failure | PASS | job `1013868`, exit 7, `passed=false`, receipt hash retained |
| First-class exact-node recovery | PASS | job `1013869`, `node03`, all four gates, `JOB_LOCAL_ABSENT` |
| Resource ceiling | PASS | 6 requested ≤ 10 authorized; 3 rounded actual minutes |
| Scheduler/ledger reconciliation | PASS | exact IDs `1013867`–`1013869`; queue empty |
| Durable and job-local cleanup | PASS | both Ceph roots absent; marked `/tmp` target absent |
| Data/firewall boundary | PASS | no development/confirmation read; only 2,947 bytes staged live |
| Evidence verifier | PASS | `A10M4O2-ACCEPTANCE-EVIDENCE-PASS` |
| Repository gates | PASS | 49 toolkit tests, shell/JSON/diff, fmt, clippy, cargo test |
