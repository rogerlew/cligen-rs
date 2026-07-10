# cligen-rs Roadmap

Status: living — forward-only queue. Completed items move to the
[work-package record](work-packages/README.md).

Ordering principles: **fixtures before port, faithful before native,
port before augmentation** (the port arc, complete) — and now, under
[ADR-0002](decisions/0002-quality-metrics-authority.md):
**instrument before adjudication, adjudication before promotion.**
No generation-behavior change is recommended before the quality
instrument has measured it at both the 30- and 100-year horizons.

## Active queue — the quality arc (ADR-0002)

| # | Item | Mechanism | Acceptance |
|---|---|---|---|
| Q2 | **Station databases in-crate + crates.io deployability** (SPEC-STATION-DB, planned; extends SPEC-PAR) | Typed station DB over the production collections (US 2015 / US 1995-legacy / international / PRISM-adjusted); query-by-location (`climNearest` successor); `cligen stations` subcommand (list / nearest / sync). Data ships **outside** the crate: hash-pinned collection manifests in-repo, payloads fetched to a local cache by the explicit `sync` subcommand only — simulation and `run` never touch the network | `cargo publish --dry-run` clean under the crates.io size limit with data excluded; a fresh `cargo install cligen` + `cligen stations sync` + `cligen run` round-trip works; collection manifests carry SHA-256 + provenance lineage; nearest-station query matches a pinned oracle set |
| Q3 | **`qc_filter` implementation + dissection + exposure adjudication** ([SPEC-GENERATION-PROFILES rev 3](specifications/SPEC-GENERATION-PROFILES.md)) | Implement `qc_filter: faithful \| off` (faithful default preserves goldens; `off` emits group-P counterfactual verdicts); run the pre-registered dissection matrix — {faithful, faithful + qc_off} × {30, 100 yr} × Q2-drawn regime corpus (arid / humid / cold / monsoonal + fixtures) — and re-baseline performance against qc_off | Dissection reports archived with the pre-registration; the convergence-vs-variability frontier quantified per horizon (incl. the per-decade early-run conditioning prediction); **adjudication recorded as ADR-0003**: is `qc_filter` user-facing, and is conditioning opt-in or opt-out per use class (30-yr agricultural vs 100-yr native)? Runspec schema rev accepts the ratified surface |
| Q4 | **Fast-batch vs legacy comparison + promotion adjudication** ([SPEC-FAST-BATCH-V1 rev 2](specifications/SPEC-FAST-BATCH-V1.md)) | Same-instrument comparison across {faithful, faithful + qc_off, fast_batch} **and legacy-Fortran `.cli` output** (Q1 post-hoc mode) on the Q3 corpus at 30/100 yr; performance case made on FMA-capable `wepp1` against the Q3 qc_off re-baseline, not against conditioned faithful | Promotion adjudicated per ADR-0002 with pre-registered bounds: either SPEC-FAST-BATCH-V1 is ratified, implemented, and the schema accepts `fast_batch_v1` — or the batch line is retired with the negative result on the record (v0 stays a closed spike either way). No production default change without a separate operator decision |

Dependencies are real, not ceremonial: Q1 (complete) is the
instrument every later item reports through; Q2 supplies the regime
corpus (and the packaging substrate) Q3/Q4 adjudicate over; Q3's
qc_off re-baseline is the denominator of Q4's performance case.

**Q1 (quality-report instrument) is complete** (2026-07-10,
[`20260710-q1-quality-report`](work-packages/20260710-q1-quality-report/package.md)):
every `cligen run` emits a `*.cli.quality.json` sidecar (groups A-D +
group P process metrics, per-decade blocks, byte-deterministic;
SPEC-QUALITY-REPORT active rev 4 with published JSON Schema), and
`cligen quality <file.cli> --par <file.par>` measures any WEPP-format
`.cli` post hoc — legacy-Fortran output included. Faithful golden
byte identity was untouched throughout.

## Deferred augmentation queue

May reorder on demand; each lands behind a versioned profile or spec.

| # | Item | Mechanism | Acceptance |
|---|---|---|---|
| A1 | **Provenance + `.cli.parquet`** (SPEC-PROVENANCE, SPEC-CLI-PARQUET) | Generation-profile block; parquet writer with provenance columns; embeds the Q1 quality report as metadata | Spec ratified; openWEPP-side consumption is openWEPP's package |
| A2 | **Native f64 mode** | Uniform-f64 engine; measured faithful↔native divergence characterization; the idiomatic destination architecture (faithful modules graduate to executable spec) | Divergence documented per variable; profile `native-f64-v1`; quality report ≥ faithful on groups A/B |
| A3 | **Observed parquet input + single-pass substitution + leap-year imputation** (SPEC-OBSERVED-INPUT) | f64 parquet observed series; variable replacement in one pass; leap-day handling | Spec + fixtures; kills the flatfile→wepppyo3→flatfile round-trip |
| A4 | **Par mutation utilities** (residual of the pulled-forward Q2) | Provenance-stamped mutation ops (PRISM localization, future-climate deltas, mean/CV scaling) over the Q2 typed DB | Mutated pars carry lineage; lineage flows into output provenance |
| A5 | **Model-structure augmentations** (was: storm-model extensions) | Modified duration/intensity derivation; NOAA design-storm curves; radiation–wetness coupling and interannual-variance mechanisms (the group-B/C structural gaps the instrument prices) | Each behind its own versioned generation profile; promotion by quality report against observed climate |
| A6 | **PyO3 surface** (SPEC-PYO3) | Python bindings, Arrow zero-copy hand-off | wepppy consumes without flatfiles |

**The faithful-mode port (items 1-8) is complete** (2026-07-09,
`20260709-output-cli-port`): `cligen run` on the 12 golden runspecs
reproduces the golden `.cli` files byte-identically. Faithful mode is
now ADR-0002 scaffolding: frozen, gated, carrying the ablation
platform for Q3 and the compatibility bridge — with its retirement
condition on record.
