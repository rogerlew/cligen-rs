# A10M5R14R2R1 — Inherited Admission-Checker Identity Remedy

Status: `EXECUTED-HOLD-FOUR-IDLE-L40-UNAVAILABLE`
Date: 2026-07-20
Evidence mode: Operational successor; unchanged R14R2 science and resources
Starting branch and push target: current `main`, push `main`

## Objective

Execute the unchanged R14R2 shared-environment four-L40 portfolio after its
authenticated zero-allocation pre-submission abort. R14R2 reached `VERIFIED`,
but the inherited R14R1 checker authenticated its own staged bytes against the
logical plan asset `admission_checker.py`. In R14R2 that name belongs to the
new outer occupancy wrapper; the inherited checker is separately staged as
`inherited_admission_checker.py`. The two files are intentionally distinct, so
the inherited self-check failed closed before the control submission.

The initial one-off compatibility approach has been deferred. It would derive
a fresh inherited checker by changing two hard-coded self-identity lookups,
but would leave the toolkit unable to express or authenticate composed checker
identities generally. A10M5O1R3 ratified the additive toolkit contract at
commit `06df84c882fbe297e93b13fb8c845d5eb500b405`. This package retains the
R14R2 closeout evidence and intended successor scope. Its executable
prepare/build/materialize implementation now consumes that ratified contract
under fresh R14R2R1 authority, budget, run, plan, and admission identities.

The implementation consumes the chain, not merely declares it. The
outer wrapper must authenticate itself as chain slot 0 and its delegate as
slot 1 against both current plan and staged manifest. The inherited checker
must derive its staged logical name from `Path(__file__)` relative to the exact
remote run root, require that name to equal slot 1, and use that logical name
for its unchanged self-byte gate. The materializer must publish the exact
ordered toolkit receipt projection. No aliasing of the inherited `__file__` to
the outer name and no removal of the inherited self-check are allowed.

## Frozen execution

The R14R2 two-role plan is retained exactly: a 30-minute one-L40 control,
followed by one 240-minute four-L40 portfolio job containing four independent
single-GPU children, plus five recovery minutes. The ceiling remains 995
GPU-minute equivalents, each primary role has one attempt and no retry, and
the xlarge evidence profile is unchanged.

Monthly and annual statistics remain error measurements rather than model
clocks. The daily OU state is continuous across month and year boundaries.
Solar and protected confirmation roles remain sealed.

## R14R2 closeout

The exact R14R2 abort receipt is retained at
`artifacts/parent-pre-submission-abort.json` with SHA-256
`7f3c7c6a9e73cb3114310cf7ecf1bcaf5ba82bc9f8cef61710f7598693d33e24`.
It authenticates source commit `3a9f2aedab1f7be5202a141c7d32350d7fe6f5e3`,
plan `7e5bf34d54a05f2055ce3ba47470488dbade732e1fe3da0d7a63ba0d670dc7e1`,
terminal `LEMHI-TOOLKIT-RUN-ABORTED-BEFORE-SUBMISSION`, exact remote absence,
and `job_local_cleanup: not_started`. The private state contained no attempts;
the resource ledger remained at genesis, so actual GPU usage was zero.

This scaffold creates no authority, reserves no compute, and submits no HPC.
Execution uses a fresh dispatch only after the scaffold is reviewed, committed,
and exact on published `main`; it consumes the ratified A10M5O1R3 contract and
does not revive the package-local substitution.

## Execution disposition

Published source `6463ab2bebcf016c371afc56e31ffc7156a2fb95` passed doctor,
probe, plan, prepare, stage, verify, and the exact composed control admission.
Control job `1017801` completed on `node03` in 1,118 seconds with exit zero,
all fourteen gates true, job-local cleanup true, and 19 charged GPU-minutes.

The portfolio was never submitted. Its immediate admission correctly rejected
the node while another user's one-GPU interactive allocation occupied one of
the four L40s. No local or remote portfolio admission was retained and no
portfolio reservation entered the ledger. The operator subsequently chose a
two-idle-L40 workflow. R14R2R2 carries the unchanged science as two concurrent
pairs; this hold is operational evidence, not a candidate result.
