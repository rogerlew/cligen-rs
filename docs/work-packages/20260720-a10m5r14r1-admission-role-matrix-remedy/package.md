# A10M5R14R1 — Admission Role-Matrix Remedy

Status: `EXECUTED-HOLD-OPERATIONAL-PREREQUISITES`
Date: 2026-07-20
Evidence mode: Operational successor; byte-identical R14 science
Starting branch and push target: current `main`, push `main`

## Objective

Execute the unchanged A10M5R14 continuous distribution-head factorial after
its authenticated zero-allocation pre-submission abort. R14 reached remote
verification but its control admission failed because the published
job-local-capacity contract did not implement the inherited admission
controller's role/wave schema. The controller consequently derived an empty
candidate matrix and rejected `exact_role_matrix` and the materialization
protocol. No job was submitted and no GPU-minute was charged.

## Operational correction

R14R1 publishes the complete contract schema consumed by the inherited
controller:

- the exact four-role candidate wave;
- control-before-candidates and close-on-observed-failure switches;
- four maximum live candidate jobs and one simultaneous bootstrap;
- one attempt, one GPU, 240 minutes per candidate, and four candidate roles;
- no arrays, distributed training, scientific retries, or recovery expansion.

The inherited controller's two-member same-wave assumption is also generalized
to authenticate every earlier member of an arbitrary-sized wave. This is
required to preserve the frozen four-candidate concurrent wave while keeping
bootstrap materialization serialized. Each later role is admitted only after
all earlier submitted same-wave roles have authenticated ready-for-science
setup receipts.

Preparation starts from the exact R14 prepared asset manifest, removes copied
admission receipts, overlays the corrected published contract and fresh
R14R1 prepare/build/materialize wrappers, and rewrites only operational
package, run, authority, budget, admission-record, and remote-root identities.

## Scientific freeze

The R14 science contract, portfolio contract, temporal contract, 188-metric
objective coverage, objective implementation, continuous and climate cores,
four candidate role scripts, seeds, sites, calendar profile, model parameter
counts, selector, thresholds, evidence profile, and science terminals remain
byte-identical. Solar and protected confirmation roles remain sealed.

Scientific terminals remain `A10M5R14-TEMPORAL-READY` and
`HOLD-A10M5R14-NO-TEMPORALLY-ELIGIBLE-CANDIDATE`.

## Resources and execution firewall

The fresh ceiling remains 995 GPU-minutes: one 30-minute control, four
concurrent 240-minute L40 candidates, and five recovery minutes. Each role has
one attempt and no scientific retry. The xlarge-evidence profile and its
256 MB expanded ceiling are unchanged.

This scaffold creates no authority, reserves no compute, and submits no HPC.
After exact publication, the existing operator authorization applies to this
bounded operational continuation.

## Execution outcome

R14R1 closed cleanly after 88 charged GPU-minutes. The control passed in 19
minutes. Candidate A and B completed their first-seed training work but failed
the parameter-ceiling firewall in 31 and 36 minutes, respectively. The model
was not actually oversized: R14's wrapper changed the inherited
`parameter_count` field from adapter-only to control-plus-adapter, after which
the unchanged caller added the 276,927-parameter control a second time. It
therefore compared 555,594 and 555,674 against the 330,000 ceiling instead of
the intended totals 278,667 and 278,747.

Candidate C failed during setup in two minutes because a third independent
environment exhausted node03's job-local filesystem. Candidate D was never
submitted and is recorded as `NOT_EXECUTED_UPSTREAM_FAILURE`. The selector was
not run because no matched four-arm portfolio exists. All partial evidence was
collected, the exact remote root and job-local roots were verified absent, the
unused recovery reserve was released, and the toolkit closed at
`LEMHI-TOOLKIT-RUN-CLOSED`.

The bounded successor is A10M5R14R2: one immutable shared environment and
corpus, four independent one-GPU child processes in a single four-L40 job, and
a corrected adapter-only/total parameter-count interface. The four scientific
arms, objective, continuous daily process, selector, and confirmation firewall
remain unchanged.

## Predecessor pin

`artifacts/parent-pre-submission-abort.json` is the exact authenticated R14
abort receipt (SHA-256
`590b69e6f2ec986d8af0f7890d43f0ce4d24d8c5e23a4a85e88bd0f3df675f23`).
It pins source commit `7b44bfae967d0f030c2f521ad5777547bb13b3b0`, plan
`2e58cd16bba1175b67a122771e46c83faa55f39ff2c0de184fe43f86351c03b6`,
terminal `LEMHI-TOOLKIT-RUN-ABORTED-BEFORE-SUBMISSION`, and remote absence.
