# AGENTS.md

Conventions and validation gates for coding agents working in cligen-rs.

## Posture

Read [docs/decisions/0001-source-code-authority-port.md](docs/decisions/0001-source-code-authority-port.md)
before touching generator code. The vendored Fortran is the faithful-mode
specification. Port fidelity questions are answered by reading
`reference/cligen532/cligen.f`, not by intuition or external CLIGEN
documentation.

## Hard rules

The normative elaboration of these rules — naming, symbol glossaries,
attribution headers, Fortran state-translation patterns, numerics
discipline — is
[docs/standards/rust-scientific-coding-standard.md](docs/standards/rust-scientific-coding-standard.md);
read it before writing port code. Summary:

- **Never enable fast-math** or float-reordering optimizations, anywhere.
- **Respect the precision map**: faithful-mode code uses f32 where the
  Fortran uses REAL*4 and f64 exactly where the source declares double
  precision. Do not "upgrade" widths in faithful paths.
- **Transcendentals in faithful paths** go through pinned
  implementations — f64 via the `libm` crate, f32 via
  `cligen::libm_pinned` — never `std` float methods. New faithful-path
  transcendentals are adjudicated empirically against captured
  reference values first (standard §1.3).
- **`reference/cligen532/` is read-only.** Fixes go upstream; refreshes
  update PROVENANCE.md.
- **Extensions declare themselves**: new behavior lives behind a
  generation profile and appears in output provenance. No silent
  divergence from faithful mode.
- Fail closed on malformed input; no inferred defaults for missing
  parameters.

## Workflow

- Work runs as work packages: `docs/work-packages/YYYYMMDD-<slug>/`
  (template in `docs/work-packages/templates/`). Fixture/spec work precedes
  implementation where either applies.
- Specs for any new interface surface go in `docs/specifications/`
  (registry in its README) with or before the implementing code.
- **Branch discipline**: execute a dispatched stage from the branch the
  kickoff prompt names and push only to its stated target (default:
  start from current `origin/main`, push `main`). If the kickoff is
  silent on branches, ask or use `main` — do not create or adopt a side
  branch for package work; that forks the package record and forces a
  reconciliation merge at review time.
- Completed roadmap items move from `docs/ROADMAP.md` to the work-package
  catalog.
- Multi-package, multi-hour, or operationally stateful changes use one living
  ExecPlan under `docs/exec-plans/`, maintained according to
  [`.agent/PLANS.md`](.agent/PLANS.md). The ExecPlan coordinates packages but
  does not replace their independent authority, evidence, or terminal state.

## Autonomy and campaign continuity

Agents are expected to advance the operator's scientific objective, not merely
administer the current package. Apply the repository's safeguards without
turning them into avoidable handoffs.

- Before declaring a package blocked or asking what comes next, inspect the
  roadmap, the package catalog, recent related packages and dispositions, and
  relevant git history. Established campaign decisions and transition patterns
  are working context, not questions to return to the operator.
- Treat an instruction to scaffold or execute a campaign stage as authority to
  perform its ordinary, reversible, in-repository follow-through: complete the
  evidence record, update the roadmap and catalog, and scaffold or execute the
  directly required bounded corrective successor when the intended scientific
  stage remains reachable. Do not stop at the first administrative boundary.
- A `HOLD` disposition records what the evidence does not yet support. It is not
  automatically a command to stop work. Preserve the hold and its artifacts,
  then continue with the simplest in-scope successor that addresses the failed
  prerequisite. Stop only when the evidence establishes a genuinely terminal
  result or the next step requires a material scientific, product, licensing,
  external-data, or destructive-action decision that has not already been made.
- Confirmation firewalls constrain access to reserved confirmation evidence;
  they do not prohibit development work. If no candidate is available, leave
  confirmation data untouched, close the confirmation package honestly, and
  continue under a new development-package identifier. A later confirmation
  attempt also receives a new identifier so versions and audit records remain
  independent.
- Do not create package theater: a package whose only result is restating an
  already-known unmet prerequisite is insufficient unless the audit itself
  produces necessary evidence. If such a package is required for traceability,
  close it minimally and proceed to the corrective scientific work in the same
  campaign sequence.
- Prefer the least complex mechanism that can answer the frozen hypothesis.
  Accept and document known data limitations when the operator has already
  judged them fit for purpose. Do not respond to sparse evidence by adding
  selectors, fallback layers, estimands, or model families unless a simpler
  bounded test has failed and the added complexity has a stated falsifiable
  purpose.
- Make reasonable choices autonomously when they are reversible and consistent
  with recorded decisions. Record the assumption in the work package. Ask the
  operator only when alternatives would materially change the scientific claim,
  public interface, compatibility contract, cost, or irreversible state.
- Report genuine blockers with the evidence already gathered, the exact
  condition that prevents progress, and the smallest decision needed. Do not
  present routine uncertainty, an unfulfilled gate, or the existence of another
  work package as a blocker.
- Execution is end-to-end: inspect inputs, implement or analyze, run the required
  gates, write artifacts and dispositions, reconcile roadmap/catalog state, and
  identify or begin the established successor. A passing command log alone is
  not package completion.

## Gates (every package)

```
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
```

For any package that adds or changes production functions in `crates/`,
additionally (adopted 2026-07-09, operator decision — present from the
first function so no burndown debt ever accumulates):

```
cargo llvm-cov --workspace --lcov --output-path target/lcov.info
cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above
```

No production function above CRAP 30. Because `CRAP = comp²·(1−cov)³ +
comp`, complexity ≥ 30 fails at any coverage — the gate is a complexity
cap plus a coverage requirement that scales with complexity. For faithful
port code this forces decomposition of large Fortran units along the
source's own internal structure, which is numerically safe in Rust
(f32/f64 values cross function boundaries exactly; there is no
excess-precision hazard) and is the decomposition the module map wants
anyway. Do not satisfy the gate by `--allow`-listing a function without a
recorded justification in the package artifacts.

Plus package-specific evidence gates (fixture identity, byte-parity on
`.cli` output, etc.). Evidence from the reference binary is valid only with
recorded build provenance (compiler, flags including `-ffp-contract=off`,
libm, source hash).

## Commit style

Imperative subject line, ≤ 72 chars, body only when the diff doesn't speak
for itself.
