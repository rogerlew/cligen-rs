# <Title>

Status: `SCAFFOLDED` | `EXECUTED-COMPLETE` | `EXECUTED-HOLD-<REASON>`
Date: YYYY-MM-DD
Evidence mode: Ran | Static | Mixed

## Objective

One paragraph: what this package changes and why now.

## Scope

Included / excluded, in enough detail that "done" is checkable.

## Authority

- For ported behavior: the `reference/cligen532/cligen.f` units and lines
  this package is faithful to.
- For extensions: the generation profile and spec (`docs/specifications/`)
  this package introduces or amends.

## Plan

Numbered phases. Fixture/spec work before implementation where either
applies.

## Data calendar and missingness preflight

Required when the package consumes calendarized observed data; otherwise state
`not applicable`. Before reserving scarce compute or starting the scientific
run, record:

- source-calendar transform ID and normalized calendar axis;
- inclusive data bounds and window-end convention;
- expected calendar-axis, observed, and masked counts;
- representative leap-year and window-boundary fixture results;
- required-field mask composition and month/year eligibility; and
- the exact preflight receipt or verifier artifact.

Never infer observational completeness from a complete date axis or a generic
"365-day" label. A10 Daymet packages must cite
`SPEC-A10-CORPUS` and its canonical calendar profile.

## Execution & dispatch

For staged multi-executor packages (the item-3/item-4 pattern): name
each stage's executor, and every kickoff/dispatch prompt **must state
the repo, the starting branch, and the push target** (normally: start
from current `origin/main`, push to `main`). A stage executed on an
unstated branch forks the package record and forces a reconciliation
merge at review time (item-4 R2 precedent).

## Gates

- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`
- Calendar/missingness preflight, when applicable, before scarce-resource use
- Package-specific evidence gates (fixture identity, spec lint, etc.)

## Exit criteria

What must be true for `EXECUTED-COMPLETE`; legitimate hold outcomes and
what each would mean.

## Artifacts

- `artifacts/` — evidence produced during execution (fixture manifests,
  run logs, review notes).
