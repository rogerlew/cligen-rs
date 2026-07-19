# Independent scaffold review

- Package: `20260719-a10m5r10r1r4-science-environment-closure-remedy`
- Reviewer: independent `portable_bootstrap_review` subagent
- Disposition: `ACCEPT`
- Review date: 2026-07-19

The reviewer authenticated the exact four-file A10M5R10R1R3 predecessor
binding at record commit `0c8222e0bbfd60d411e884375f3a4fde4cd04441`,
confirmed fresh R1R4 package/run/authority/budget/token identities, and found no
copied R1R3 result artifacts.

Both science launchers contain the same seven-variable parent environment
closure after the executed child bootstrap and before every parent-side Python
process. The closures clear and assert all three prohibited names and normalize
exactly to `REQUIRED_JOB_ENVIRONMENT`. The reviewer confirmed that the exact
R1R3-to-R1R4 delta guard, real hostile-child/ambient process-scope regression,
and per-assignment mutation guards cover this remedy while `submit_v2.sh`
retains `--export=NONE`.

The reviewer independently reran the freeze and science verifiers, all 27
package tests, and shell syntax checks. The frozen science, corpus, calendar,
roles, waves, one-attempt policy, and 935 GPU-minute ceiling remain unchanged.
No concrete findings remain.

Disposition: the scaffold is accepted for operator-controlled execution.
