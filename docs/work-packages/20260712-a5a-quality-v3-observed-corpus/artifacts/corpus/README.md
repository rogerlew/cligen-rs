# A5a observed-target corpus build

This directory is the reproducible build record for
`cligen-a5a-observed-v1`. The checked-in source archives live under
`references/observed/a5a-v1/`; mutable upstream URLs are locators only.

The target builder requires Python 3.11 or newer (`tomllib`). The offline
schema gate additionally requires `jsonschema == 4.23.0`. Populate the Cargo
cache and Python environment once before disconnecting. The exact Rust/Cargo
compiler identity is recorded under `metric_estimator.compiler` in
`manifest-v1.json`; confirm `rustc --version --verbose` matches it. The
repository's moving `stable` selector resolved to Rust 1.95.0 for this build.
If `stable` has advanced, install and select 1.95.0 (for example,
`rustup toolchain install 1.95.0` followed by
`export RUSTUP_TOOLCHAIN=1.95.0`) before rebuilding.

```sh
repo=$(git rev-parse --show-toplevel)
cd "$repo/docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/corpus"
cargo build --locked --offline --bin cligen-quality-estimator
python3 build_target_schema.py
python3 acquire_sources.py
python3 build_targets.py \
  --metrics-helper "$repo/target/debug/cligen-quality-estimator"
python3 build_coverage.py
python3 finalize_manifest.py
python3 verify_offline.py
```

`acquire_sources.py --network` is the one-time acquisition path. It refuses to
replace a differing archive. All 17 Daymet objects must match their Q3 source
hashes. The eight GHCN objects are a new 2026-07-12 snapshot; their prior Q3
hashes remain recorded separately and are not overwritten.

The builder uses fixed 1980–2025, 1980–2009, and 2010–2025 bounds. It does not
impute missing values. Monthly or annual multivariate targets therefore have
small or zero GHCN sample sizes at several stations; those nulls and sample
counts are evidence, not repaired data. Daymet supplies all 17 complete
primary products. Daily sources cannot identify CLIGEN duration,
time-to-peak, or peak-ratio targets, so every such block is explicitly
unavailable.

Quantiles use the metrics-v3 empirical inverse-CDF nearest-rank estimator.
Annual rolling maxima use consecutive source-calendar windows, may cross a
December/January boundary, and are attributed to the window's end year; only
complete precipitation years enter their distributions. R1mm spells cross
month and year boundaries, are classified by start month, and terminate at an
observed gap. The low-frequency statistic is centered positive-frequency DFT
power at periods of at least four years divided by all positive-
frequency power. A series with fewer than four complete years, zero nonzero-
frequency power, or any missing year between its first and last complete year
is null. Missing GHCN years are never compressed into an evenly sampled DFT;
lag-one dependence still uses every genuinely consecutive year pair.

The low-frequency calculation is delegated to the same Rust metrics-v3
estimator used for generated reports. Its f64 sine/cosine calls use the
Cargo-locked `libm` implementation rather than the Python build host's
platform math library. The final manifest binds the helper source, metrics
source, Rust toolchain file, Cargo inputs, and exact `libm` package identity.
Python and operating-system fields remain informational build provenance;
they do not define the estimator semantics.

Every station/source/period precipitation block contains a `coverage` record.
`expected_days` is the number of dates in the closed period under the source
calendar; `observed_precip_days` counts dates with accepted precipitation;
`missing_days` is their difference; and `missing_gap_runs` counts maximal
contiguous intervals of missing expected source-calendar dates, including an
interval touching either period boundary. Spells close before a missing date,
adjacent-day correlations require consecutive source-calendar dates, and
rolling windows containing any missing date are excluded. Thus no daily
structure statistic silently bridges a gap.

`coverage-evidence-v1.md` is the compact 102-row audit ledger (17 stations ×
two source products × three periods). It records unavailable products as
such and binds its source manifest, target corpus, target builder, and coverage
derivation tool by SHA-256. The final manifest and `SHA256SUMS` bind the ledger
in turn.

Package-local Draft 2020-12 schemas under `schemas/` validate the build
configuration, source manifest, and final lineage manifest. The public target
uses `docs/specifications/observed-target-corpus-v1.schema.json`. The offline
gate checks all four schemas with `jsonschema`, verifies their own validity,
and hash-binds the package-local schemas in the final manifest. The manifest
also binds the archive documentation and third-party data notice. The
repository's Apache-2.0 license does not relicense the archived Daymet or
GHCN-Daily data; their provider citations and use conditions are recorded in
`references/observed/a5a-v1/THIRD_PARTY_DATA_NOTICE.md`.
