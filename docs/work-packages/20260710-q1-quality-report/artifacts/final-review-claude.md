# Stage R2 — Final Review and Closure (Claude Code)

Date: 2026-07-10
Evidence mode: **Ran** for every gate row (exit codes checked
directly, never through a pipe); **Static** for the targeted reads,
cited inline.

## Gates re-run independently (post-remediation tree)

| Gate | Result | Exit |
|---|---|---|
| `cargo fmt --check` | clean | 0 |
| `cargo clippy --all-targets -- -D warnings` | clean | 0 |
| `cargo test --release` | **88 passed, 0 failed** (Stage C's 87 + the R2 calendar vector); 12/12 golden `.cli` byte identity through both the library gate and the binary gate with sidecars | 0 |
| `CLIGEN_FMT_SWEEP=/workdir/cligen-rs/target/stage-c-fmt/fmt_pairs.txt cargo test --release -- --ignored` (absolute path per C-R1-004) | 9 passed, 0 failed, incl. the 57,341,160-field format sweep | 0 |
| `cargo llvm-cov` | TOTAL 89.99% regions / 85.42% functions / 92.19% lines | 0 |
| `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**' --fail-above` | 293 functions; none above 30; no allow-lists | 0 |
| `cargo deny check` | advisories, bans, licenses, sources ok | 0 |

## Targeted reads (Static)

- **Observation-only claim verified** in `rng.rs::ranset` (rejection /
  acceptance / cap-give-up recording strictly after the source
  verdicts; the give-up `println!` untouched; acceptance statistics
  copy the existing `ranset_quality_levels` outputs with no new float
  computation), `randn_observed` (counter increment after the source
  draw), `gen_precip` (v7 recovery), `dstg` (returned deviates only),
  `timepk` (observed k10), `burn_observed`, and `generation_setup`.
  No counter value is read anywhere in generation code.
- **Plumbing**: `run_to_cli` → `RunOutput { cli, process }`;
  `PreparedRun::generate()` retains the text-only surface;
  `generate_and_write` passes the counters into `compute_report`;
  `cligen quality` passes `None` — post-hoc reports keep
  `process: null`. The `.cli` byte path is unchanged (confirmed by
  the gates, not just the read).
- **Schema**: draft 2020-12, properties in Rust serialization order,
  `additionalProperties: false` throughout (32 occurrences),
  structurally validated in-test over post-hoc, single-event,
  faithful-run, and fast-run reports without a new dependency.
- **Cap-hit fidelity**: Stage C's New Meadows census (3,348 accepted
  batches, 7 cap give-ups, the 7th silent because the shared `iredo`
  was already capped) matches the source's shared-counter semantics
  the spine handoff flagged.

## R1 dispositions (findings from `review-codex.md`, verbatim IDs)

| # | Sev | Disposition | Action |
|---|---|---|---|
| C-R1-001 | MEDIUM | **ACCEPTED — remediated in R2.** The intake accepted impossible dates (Feb 31). | `quality::intake::max_day`: month-specific day bounds; February 29 accepted iff the printed year is divisible by 4 — proven as the exact union of the source's two leap surfaces (daily-mode Gregorian on the printed year; storm-mode century `nt` test), which is what a mode-blind post-hoc intake must accept. New vector `impossible_calendar_dates_fail_closed` (rejects Feb 31/Feb 30/Feb 29-y3/Apr 31/day 0; accepts Feb 29 in years 4, 100, 1900, 2000). Adjudication §3a records the rule. |
| C-R1-002 | MEDIUM | **ACCEPTED — remediated in R2.** `f64::powf` is not a pinned surface. | `adjusted_skew` computes `m2^1.5` as `m2 * m2.sqrt()` — both operations IEEE-754 correctly rounded, hence platform-independent bytes. ≤ 1-2 ULP shift vs the Stage S emission; no committed report fixtures existed, so no churn. Adjudication §3a. |
| C-R1-003 | HIGH | **ACCEPTED — contract conflict adjudicated.** The active spec promised fast-v0 off-style counterfactuals that the package scope (and kickoff) assigned to Q3. | SPEC-QUALITY-REPORT → **rev 4**: counterfactual verdicts (for `qc_filter: off` and for `fast_batch_v0`) begin with Q3, which owns the metrics-version consequence of adding the field; metrics_version 1 carries the null plus counters only. The Q1 schema and Rust types are therefore complete as published. Registry updated. |
| C-R1-004 | LOW | **ACCEPTED — evidence-command correction, including of my own record.** | Stage S `gate-results.md` transcribed the sweep path as relative although the command run used the absolute path; the row is corrected with a correction note, and the R2 gate above records the reproducible absolute-path form. |

## Closure

All four findings dispositioned (4/4 accepted; two remediated in
code, one by spec rev 4, one by evidence correction). Gates green on
the final tree. Faithful golden byte identity held through every
stage. Package → `EXECUTED-COMPLETE`; Q1 leaves the ROADMAP for the
work-package catalog.

Residuals on the record (not blockers, named per the truthfulness
rule): cross-platform report byte identity is now argued from
IEEE-correctly-rounded operations (Static), not demonstrated on a
second platform (no such platform in this environment); the in-test
schema validator covers the keywords the schema uses, not all of
draft 2020-12; `qc_filter: off` counterfactuals and their
metrics-version consequence are Q3's.
