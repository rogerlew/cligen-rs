# Repository ExecPlans

An ExecPlan is a self-contained, living implementation document for work that
spans multiple milestones, packages, or external execution environments. A
novice with only the repository and the plan must be able to understand the
purpose, execute the work safely, verify observable behavior, and resume after
an interruption.

ExecPlans live in `docs/exec-plans/`. A plan may govern more than one work
package, but every package retains its own authority, gates, evidence, and
terminal disposition.

## Required qualities

Explain the user-visible outcome first. Define repository-specific terms in
plain language and name every important file with a repository-relative path.
Resolve material design choices in the plan instead of leaving them to a later
executor. Describe exact commands, working directories, expected observations,
validation, safe retry behavior, and cleanup.

Keep the plan current while executing it. Someone resuming from the plan must
not need the original conversation or unstated memory. Revise every affected
section when discoveries change the design, and append a short revision note
at the end explaining the change.

## Required sections

Every ExecPlan contains these sections:

- `Purpose / Big Picture`
- `Progress`, with timestamped checkboxes
- `Surprises & Discoveries`
- `Decision Log`
- `Outcomes & Retrospective`
- `Context and Orientation`
- `Plan of Work`
- `Concrete Steps`
- `Validation and Acceptance`
- `Idempotence and Recovery`
- `Artifacts and Notes`
- `Interfaces and Dependencies`

Milestones are narrative and independently verifiable. Each milestone states
what new behavior exists, how to exercise it, and what observation constitutes
acceptance. Progress records granular state; it does not substitute for the
milestone narrative.

## Safety and evidence

Prefer additive, repeatable work. If an external operation can partially
complete, specify how identity is reconciled before retry. Never reset a
resource ledger, invent a successor authority, or broaden a work package to
escape a failed gate. Record concise transcripts and hashes that demonstrate
behavior without publishing credentials, private paths, raw restricted
evidence, or another user's files.

An ExecPlan is complete only when the behavior works end to end, repository
gates pass, external resources are reconciled and cleaned when applicable, all
governed work packages have honest terminal states, and the retrospective
compares the result with the original purpose.
