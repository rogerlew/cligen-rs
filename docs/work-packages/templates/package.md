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

## Gates

- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo test`
- Package-specific evidence gates (fixture identity, spec lint, etc.)

## Exit criteria

What must be true for `EXECUTED-COMPLETE`; legitimate hold outcomes and
what each would mean.

## Artifacts

- `artifacts/` — evidence produced during execution (fixture manifests,
  run logs, review notes).
