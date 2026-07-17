# Risk and access register

| Risk | Control | A10M0 disposition |
|---|---|---|
| Password/Duo exposure | Human performs MFA; automation uses existing control masters with `BatchMode=yes` | Frozen |
| Stale public cluster docs | Timestamp and retain live Slurm/module/driver receipts | Carried to A10M2 |
| Wrong priority/accelerator | Require `icrews`, `gpu-icrews`, and typed `gpu:l40` before submission | Carried to A10M2 |
| Preemption disrupts test | Check policy; checkpoint; never deliberately displace a job | Carried to A10M2 |
| Compute-node network unavailable | Freeze and hash an offline wheelhouse after J1 driver receipt | Carried to A10M2 |
| Resource overrun | Five-job ledger, at most one exact transient rerun, hard one-GPU-hour stop | Frozen |
| Confirmation leakage | No target-series access before candidate seal; sanitize all receipts | Frozen |
| Dependency drift | Pin framework stack; record inherited A9 scikit-learn omission | Open debt, nonblocking for M2 |
| Credential/path leakage | No environment dumps, keys, sockets, usernames, or absolute operator paths in artifacts | Frozen |
