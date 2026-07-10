# Stage R2 — Final Review (Claude Code)

Date: 2026-07-09
Reviewer: Claude Code
Scope: Codex Stage C (`609c953`) + R1 disposition; package closure.
Evidence mode: labeled per item.

## Verdict

**CLOSE — `EXECUTED-COMPLETE`.** No findings. With this package,
ROADMAP items 1-8 — the entire faithful-mode port — are complete.

## Gates re-run independently (Ran, this session)

| Gate | Result | Exit |
|---|---|---|
| `cargo fmt --check` | clean | 0 |
| `cargo clippy --all-targets -- -D warnings` | clean | 0 |
| `cargo test --release` | 17 suites ok — includes `runspec_cli` (binary-level 12/12 golden byte parity) and the 9 runspec vectors | 0 |
| `CLIGEN_FMT_SWEEP=<my Stage S capture> cargo test --release -- --ignored` | all identity suites + cold-start replay + full 57.3M-field format sweep ok | 0 |
| `cargo llvm-cov` + `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` | 217 functions, 0 above CRAP 30 | 0 |
| `cargo deny check` | advisories / bans / licenses / sources all ok | 0 |

Independent-capture note: my ignored-suite re-run used the **Stage S
probe capture** (SHA-256 `df8596f4…7777`); Codex's Stage C run
regenerated its own capture and recorded the **same SHA-256** — the
probe generation is reproducible across executors.

## By-hand executional check (Ran)

Built the release binary and ran
`cligen run crates/cligen/tests/fixtures/runspec/jeogla-au-seed17/inp.yaml`
directly; `cmp` against the golden: **byte-identical**. The K-S QC
`*** ERROR ***` messages appear on the screen surface exactly as the
legacy binary prints them — not part of the `.cli` contract.

## Targeted reads (Static)

- **Runspec module boundary**: `runspec.rs` resolves paths lexically
  against the document directory, opens/parses inputs, and hands
  `run_to_cli` a fully resolved `RunInputs` — the structure constraint
  held (`run_to_cli` unchanged, still CRAP 29.0; runspec logic in its
  own module; binary is a 41-line clap shim).
- **Mode mapping + storm calendar**: continuous/observed/single_storm/
  design_storm → iopt 5/6/4/7; storm-date validation uses the
  source's own quirky iopt-4/7 leap predicate (`&&`, not `&& !` —
  `source_storm_leap_year` matches wxr_gen:3759-3763), distinct from
  the Gregorian daily predicate. Design storm fills date+amount only,
  `usdur`/`ustpr`/`uxmav` defaulted — consistent with the item-6
  sing_stm typed intake (iopt-4-only fields).
- **Observed resolution**: `begin_year` defaults from
  `PrnReader::initial_year` (fail-closed, ≥ 1 enforced), explicit
  `simulation.begin_year`/`years` act as overrides, `years` defaults
  100 — all per SPEC-RUNSPEC rev 2 (§observed years = cap).
- **Canonical echo**: renders `-rN -i<par> -O<prn> -o<cli> -t<mode>
  -I<n>`, each only when non-default (`-o` suppressed for `wepp.cli`,
  `-t` suppressed for continuous, `-I` suppressed for none) — matches
  §Header echo canonical order. Golden fixtures pin `command_echo`
  verbatim; spot-checked mt-wilson-seed17 and single-storm-seed17
  against the SPEC golden-equivalence table — exact.
- **Validation posture**: `deny_unknown_fields` on every document
  struct; field-path errors via `serde_path_to_error`; exactly-one-
  YAML-document enforced; storm scalars f32-narrowed with finiteness
  checks; `validate` never touches the output path (asserted in the
  integration test); `run` honors `output.overwrite` via
  `create_new(true)` — never a prompt.
- **deny.toml**: allow-list Apache-2.0 / MIT / BSL-1.0 (Boost) /
  Unicode-3.0 — all permissive; new deps (clap, serde, serde_yaml,
  serde_path_to_error) fit. No copyleft.

## R1 disposition

R1 reported PASS with no findings. I verified its two Ran claims
independently (binary golden parity; full format sweep) — both
reproduce. No disposition items.

## Closure

Package status → `EXECUTED-COMPLETE`. ROADMAP updated: item 8 leaves
the queue; the A-series (A1 provenance/parquet first) is now the head
of the roadmap.
