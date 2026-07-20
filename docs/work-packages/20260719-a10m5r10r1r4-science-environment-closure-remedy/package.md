# A10M5R10R1R4 — Science Environment Closure Remedy

Status: `EXECUTED-COMPLETE`
Date: 2026-07-19
Evidence mode: Mixed
Starting branch and push target: current `main`, push `main`

## Objective

Execute a fresh, coherent rerun of the complete A10M5R10 architecture
portfolio without changing its models, stochastic objective, corpus, calendar,
role matrix, seeds, resources, admission policy, portable bootstrap, or
selector. This package corrects the A10M5R10R1R3 process-scope failure by
reconstructing the complete frozen science environment in both parent science
launchers after portable bootstrap and before any parent-side Python process.

## Predecessor evidence and frozen science

A10M5R10R1R3 authenticated source, assets, authority, plan, staged remote
tree, login admission, portable Python 3.11.15, environment installation,
setup-payload deletion, corrected corpus extraction, calendar preflight, and
job-local cleanup. Control job `1014056` reached the first P1 training batch's
output-head linear operation. PyTorch deterministic-algorithm enforcement then
failed because `CUBLAS_WORKSPACE_CONFIG=:4096:8` had been exported only by the
executed `bootstrap_environment.sh` child. Slurm launched the parent wrapper
with `--export=NONE`, so the child could not alter the environment inherited by
`materialize_controls.py` or its `train.py` subprocess.

No control row completed, no candidate was admitted, and no selector ran.
This package binds the exact committed R1R3 HOLD at record commit
`0c8222e0bbfd60d411e884375f3a4fde4cd04441`, including:

- `operational-summary.json`: 2,418 bytes, SHA-256
  `bbf5b6c1bc6dc710dc89a3d343b4c2eb073b3777fbc3b8e27716c58c6c6b68d2`;
- `execution-disposition.md`: 1,600 bytes, SHA-256
  `bf80f1f722b0d8adb8b03c2138d06873e5fc6fc6c2e7bb3731f4222a232507b6`;
- `cleanup-record.json`: 701 bytes, SHA-256
  `9dc709bfba895255b5f72e5951fd71bb73ca6445283de0a69e9a326589544d8c`;
  and
- `resource-ledger.md`: 808 bytes, SHA-256
  `050090ca4d2ecb86121f494d9fa73401162ca041c8b36885d12cf4bd7c91be5e`.

The earlier R1R2, R1R1, R1, and independently reviewed A10M5O1R2 toolkit
bindings remain in `artifacts/predecessor-evidence-identities.json`. The twelve
direct and transitive science dependencies remain byte-identical to the
original A10M5R10 portfolio. The complete 1,440-object Daymet calendar and
missingness preflight remains byte-identical and precedes resource reservation.

## Frozen parent science environment remedy

The R1R3 plan already froze seven required job-environment values. Repairing
only CuBLAS would leave the other six values absent or accidental in the
parent process and would not satisfy the declared environment closure. Both
`run_control.sh` and `run_candidate.sh` therefore perform the same bounded
sequence immediately after successful child bootstrap and before any
parent-side Python:

1. clear `PYTHONPATH`, `PYTHONHOME`, and `LD_LIBRARY_PATH`;
2. export exactly the required CuBLAS, interpreter path, pip-cache,
   no-user-site, temporary-directory, Torch-cache, and XDG-cache values; and
3. assert every required value and the absence of all three prohibited names.

The runtime realization is normalized to the already-frozen plan contract:

| Name | Wrapper value | Normalized plan value |
| --- | --- | --- |
| `CUBLAS_WORKSPACE_CONFIG` | `:4096:8` | `:4096:8` |
| `PATH` | `$environment/bin:/usr/bin:/bin` | `/registered/run/runtime/bin:/usr/bin:/bin` |
| `PIP_CACHE_DIR` | `$job_local/pip-cache` | `/registered/job-local/attempt/pip-cache` |
| `PYTHONNOUSERSITE` | `1` | `1` |
| `TMPDIR` | `$job_local/tmp` | `/registered/job-local/attempt/tmp` |
| `TORCH_HOME` | `$job_local/torch-cache` | `/registered/job-local/attempt/torch-cache` |
| `XDG_CACHE_HOME` | `$job_local/cache` | `/registered/job-local/attempt/cache` |

`PIP_NO_INDEX`, `PIP_NO_CACHE_DIR`, `CC`, and `CXX` remain setup-only child
bootstrap controls because they are not members of the frozen parent science
environment. The bootstrap remains an executed child; no sourcing semantics,
fallback environment, ambient inheritance, or weakening of deterministic
PyTorch is introduced.

The corrected R1R3 corpus extraction remains unchanged:

```sh
tar -xf "$run_root/corpus.tar" -C "$job_local"
```

The canonical archive remains 224,040,960 bytes with SHA-256
`8770e127f8413eedd47d50670c359e450988444a8c4d8d43ca5645619a1b0a17`,
101 safe relative members, the sole `corpus/` prefix, 98 accepted objects, and
three required manifests. The R1R4 package-specific layout pin is itself
frozen at 864 bytes and SHA-256
`ea17be0acecc8afc99714c1c9df42511440382c2b8fb6d0511b0aad3414069d3`.

## Authority and resource bound

The package defines fresh package, run, authority, budget, and scheduler-token
identities. It permits one 30-minute one-L40 control predecessor, ten
90-minute single-attempt one-L40 candidate roles in the unchanged five ordered
waves of two, and one five-minute exact-node recovery reserve: the unchanged
935 GPU-minute ceiling. There are no retries, arrays, multi-rank jobs,
substitutions, or prior-result splicing.

## Gates

- the exact committed R1R3, R1R2, R1R1, R1, and A10M5O1R2 evidence bindings
  authenticate and their terminal semantics pass;
- all twelve science dependencies and the complete calendar/missingness
  preflight remain byte-identical;
- corpus identity, safe layout, corrected extraction destination, and
  pin-of-pin authentication remain passing;
- both parent wrappers contain byte-identical seven-variable closure blocks,
  ordered after bootstrap and before the first parent Python;
- a real subprocess regression begins from an explicitly bounded environment,
  runs a child bootstrap that exports hostile sentinel values, and proves both
  parent wrappers reconstruct the exact normalized seven-variable contract
  while clearing all prohibited names;
- deleting or changing any required wrapper assignment fails the source guard;
- the normalized R1R3-to-R1R4 wrapper diff contains only the environment block
  and fresh terminal identity labels;
- `submit_v2.sh` retains `sbatch --export=NONE`;
- portable bootstrap, terminal finalizers, admissions, evidence closure,
  roles, waves, one-attempt policy, and 935-minute arithmetic remain frozen;
- package, science, freeze, toolkit, shell-syntax, JSON, whitespace, Cargo
  formatting, Clippy, and test gates pass.

Coverage/CRAP is not triggered because this package changes no production
function under `crates/`.

## Result

The full matrix completed and the frozen selector issued
`A10M5R10-PORTFOLIO-READY`. All six controls were reconstructed exactly; all
ten family/capacity roles and 30 seed rows passed their execution and evidence
gates. Four configurations were eligible and nondominated. The selector
retained `annual_monthly_residual_adapter-k1`,
`monthly_residual_adapter-k2`, and
`annual_monthly_residual_adapter-k2` in its predeclared three-axis order.

The result supports the centered residual-adapter mechanism, with explicit
annual/monthly structure useful at both capacities. Hierarchical joint-factor
K2 was also eligible and nondominated but lost an equivalence-band parsimony
tie-break; it was not scientifically rejected. Climate-normal state space
failed combined-dispersion and daily-NLL guards. The physics-conditioned arm
improved solar dependence aggregates but failed core dispersion and per-block
solar non-degradation, so broader physics coupling is not retained in this
form.

The selector replay was byte-identical. The toolkit authenticated all 153
allowlisted evidence files, settled 396 actual GPU-minutes, released the unused
recovery reserve, verified job-local absence, removed the exact durable root,
and closed normally. Confirmation remained sealed. Independent execution
review accepted the final record with no findings.

## Exit criteria

Scientific terminals remain exactly those frozen by A10M5R10:
`A10M5R10-PORTFOLIO-READY`, `HOLD-A10M5R10-SINGLE-CANDIDATE`,
`HOLD-A10M5R10-NO-CANDIDATE`, or an exact calendar, identity, role, support,
evidence, resource, or cleanup hold. An operational failure records an exact
`HOLD-A10M5R10R1R4-*` condition without interpreting candidate science.

## Artifacts

- `artifacts/job-local-capacity-contract.json` — unchanged science and resource
  policy plus the exact parent environment realization;
- `artifacts/predecessor-evidence-identities.json` — exact R1R3 and inherited
  predecessor evidence bindings;
- `artifacts/science-dependency-identities.json` and
  `artifacts/verify_science_identity.py` — unchanged science freeze;
- `artifacts/calendar-preflight.json` — complete calendar and missingness
  preflight;
- `artifacts/corpus-layout-pin.json` and
  `artifacts/verify_corpus_layout.py` — retained corpus identity/layout gate;
- `artifacts/admission-protocol.md` — login admission, portable bootstrap,
  parent environment closure, corpus extraction, and stop-matrix procedure;
- `artifacts/verify_freeze.py` — science, environment, predecessor, corpus,
  interpreter, execution-policy, and normalized-delta verifier;
- `artifacts/scaffold-review.md` — independent review scope and final `ACCEPT`
  disposition;
- `artifacts/portfolio-summary.json`, `portfolio-pareto.json`,
  `portfolio-decision.json`, and `portfolio-selection-evidence.json` — complete
  frozen selector inputs and outputs;
- `artifacts/operational-summary.json`, `execution-disposition.md`,
  `resource-ledger.md`, and `toolkit-records.md` — reconciled execution,
  science, accounting, and closure records;
- `artifacts/toolkit-recovered/` — sanitized collection, cleanup, and terminal
  receipts;
- `artifacts/verify_result.py`, `gate-results.md`, and `review.md` — result
  verification and independent final disposition;
- `artifacts/test_admission_checker.py` and
  `artifacts/test_operational_identity.py` — retained and corrective regression
  tests; and
- `artifacts/jobs/` — immutable asset preparation, control records, admission,
  portable bootstrap, durable diagnostics, parent launchers, and frozen
  science sources.
