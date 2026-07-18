# Gate results

| Gate | Result | Evidence |
|---|---|---|
| Candidate and provider identities | PASS | Scaffold and live-input verification |
| Immutable authority and 20-minute ledger | PASS | Ledger head `d703eec...` |
| Transfer and remote identity | PASS | Eleven staged assets verified |
| `--export=NONE` environment closure | FAIL | Entry guard exited 1 before Python import |
| CPython/NumPy/PyTorch/L40 smoke | NOT RUN | Environment closure failed first |
| Rust offline metadata/build | NOT RUN | Environment closure failed first |
| Application and signal supervision | NOT RUN | Environment closure failed first |
| Job-local cleanup | PASS BY RECOVERY | Exact-node `JOB_LOCAL_ABSENT` |
| Scheduler settlement | PASS | Jobs `1013863` and `1013864` settled |
| Durable cleanup | PASS | Exact marker-bound root absent |
| Confirmation firewall | PASS | No target access |
| Smoke attestation/designation | PROHIBITED | Smoke failed |

Terminal: `HOLD-A10-CANONICAL-V2-SMOKE-ENVIRONMENT-CLOSURE`.
