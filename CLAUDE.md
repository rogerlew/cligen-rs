# CLAUDE.md

> Claude Code operating guide for cligen-rs. Lean by design — amend as the
> project earns complexity.

## Authorship

This document and all CLAUDE.md files are maintained by Claude Code, which
retains full authorship rights for CLAUDE.md content.

## Role boundary

Same split as openWEPP: **Codex** authors code by default; **Claude Code**
owns documentation, architecture/design guidance, debugging and root-cause
analysis, review, and may run work packages end-to-end (code included) when
the operator directs it.

## The one thing to hold onto

This is a **source-code-authority port**
([ADR-0001](docs/decisions/0001-source-code-authority-port.md)) — the
opposite posture from openWEPP. The pinned Fortran at `reference/cligen532/`
is the specification for faithful mode; do not "correct" its behavior
against physical intuition or external descriptions. Extensions are labeled
divergences behind versioned generation profiles, never silent improvements.
If you find what looks like a bug in the Fortran: record it, test-pin the
behavior, and raise whether faithful mode preserves it (usually yes) and
whether a profile should fix it (operator decision) — the ksatadj lesson
from openWEPP applies here with the sign flipped.

## Debugging playbook

- Faithful-mode divergence: run the trajectory differ; localize to first
  divergent day/variable; suspect, in order — transcendental (libm)
  mismatch, precision-map error (f32 vs f64 site), transcription error,
  reference-build contamination (FMA contraction, wrong flags).
- Never debug faithful mode with aggregate statistics; they cannot localize
  a bifurcation.
- The Fortran's built-in QC (`chitst`, `ks_tst`) is a distributional
  cross-check, not an identity oracle.

## Truthfulness

openWEPP's discipline applies verbatim: verbs match evidence ("ran" only if
run), evidence labeled Ran/Static, delegated runs attributed, skipped
execution surfaced with its cost.

## Pointers

- [README.md](README.md) — identity and layout
- [docs/ROADMAP.md](docs/ROADMAP.md) — forward-only queue
- [docs/port/fortran-decomposition.md](docs/port/fortran-decomposition.md) — decomposition map
- [AGENTS.md](AGENTS.md) — Codex conventions and gates
