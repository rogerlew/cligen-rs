# A10M2 execution dispatch

Date: 2026-07-16 PDT

- Repository: `cligen-rs`
- Starting branch and push target: `main`
- Published starting commit:
  `922e81f3530d827f591265fe80c3520e76c61ce9`
- Accepted predecessor: `A10M0-PREDECESSORS-FROZEN`
- Operator authority: `Execute A10M2`
- Base matrix: J1, J2, J3, J4a, J4b; 40 requested GPU-minutes
- Retry rule: at most one exact infrastructure-transient rerun, no more than
  10 requested GPU-minutes
- Hard package ceiling: one GPU-hour

Both `login-ui` and `lemhi` control masters were live immediately before the
execution preflight. MFA remains human-supervised; all automated SSH commands
use `BatchMode=yes` and contain no authentication material.
