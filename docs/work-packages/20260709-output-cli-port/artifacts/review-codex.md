# R1 Cross-review — Codex

Date: 2026-07-09
Reviewer: Codex
Scope: Stage S spine plus Stage C runspec/CLI boundary.
Evidence mode: Static except where marked Ran.

## Result

PASS — no findings.

## Format fidelity

Static: `output.rs` retains the Stage S writer's exact-field route through
`fortran_format::{f_edit,i_edit}`. The header receives `command_echo` as
text and writes precisely the one historical trailing blank documented
from `cligen.f:670-682`; it does not parse, normalize, or reformat the
echo. Stage C supplies an explicit echo verbatim, and its canonical form
only when absent.

Ran: the binary `cligen run` test compared all twelve complete output
files byte-for-byte with their golden files. The full 6,371,240-line
format probe capture (57,341,160 fields) also passed the ignored format
identity test with the recorded checksum in `stage-c-report.md`.

Finding: none.

## Orchestration fidelity

Static: runspec mode mapping is `continuous → iopt 5`, `observed → 6`,
`single_storm → 4`, and `design_storm → 7`. Storm-date validation uses
the distinct iopt-4/7 predicate at `wxr_gen:3758-3763`, while the
unchanged `run_to_cli` retains the daily Gregorian predicate and yearly
zeroing/stop protocol at `wxr_gen:3773-3808`. The runspec boundary only
provides fully resolved `RunInputs`; it does not grow `run_to_cli`.

Ran: constructed vectors cover the source-calendar February branch,
design-storm intake, observed defaults and explicit observed years, and
both non-golden interpolation selections.

Finding: none.

## SPEC-RUNSPEC conformance

Static: all document objects use `deny_unknown_fields`; schema version,
closed enums, conditional blocks, non-empty paths, integer domains,
f32-convertible finite storm values, and source-calendar dates report
their field paths. `validate` resolves paths against the supplied
document directory, opens/parses inputs, and never accesses the output;
`run` applies `output.overwrite` with `create_new` when false.

Ran: integration vectors cover missing/wrong-mode blocks, unknown and
wrong-typed fields, scalar domains, canonical echo, output refusal and
overwrite, output-free validation, and symlinked-document path
resolution. All twelve golden runspec fixtures validate and run through
the public binary surface.

Finding: none.

## Test and evidence alignment

Static: new runspec tests exercise the binary rather than only the
library seam, while the existing library parity test remains intact.

Ran: Stage C's gate record is in `stage-c-report.md`; the quality gates,
coverage/CRAP threshold, dependency-policy check, full format sweep, and
all golden byte comparisons passed.

Finding: none.
