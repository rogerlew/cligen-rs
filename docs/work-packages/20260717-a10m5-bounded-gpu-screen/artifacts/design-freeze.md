# A10M5 prospective design freeze

This record completes implementation details left parametric by A10M3. It does
not change its grid, roles, objectives, seed, thresholds, or resource ceiling.
It was committed before any A10M5 fit output or target access.

## Identity and firewall

- Scientific contracts: `a10m3-model-training-generation-v1` and
  `a10m3-selector-benchmark-v1` unchanged.
- Scientific model-record runtime identity: `lemhi-a10-py311-l40-v1` at
  `0b1115a6801259c62d9550c877a3c49a897319348ba1c2027be0d9c4f77c1179`,
  retained because schema v1 is immutable.
- Operational toolkit designation: `lemhi-a10-py311-l40-v2-candidate` at
  `5addee9c5db3592ee247eab2b5266ed5567fd9aaf24ed78dcb321ecbb001e22d`,
  selected by designation revision 1 and attestation `5caf106a...`.
- Corpus: accepted A10M1 v2 transfer (98 objects; 223,799,545 bytes), normalized
  manifest, and candidate-fit-only normalization identities.
- Readable roles: `candidate_fit` and `fit_validation`. The runner rejects
  `development`, `confirmation_metadata`, and `confirmation_locked` paths.

## Epoch, sampling, and missingness completion

One screen epoch is exactly 12 batches of 64 windows: two batches from each of
the six regimes in fixed round-robin order. Within a regime the sampler gives
equal probability to each available source class, then equal probability to a
station/tile, then equal probability to each eligible 730-day window at
365-day offsets. A source with no supported seven-output target window in a
regime contributes no fabricated sample; its absence is recorded. All
selected target fields must be finite through input day 730 and target day
731. Intentional missing rows make that window ineligible and are never filled.

Validation enumerates every eligible 365-overlap window from every accepted
Daymet `fit_validation` point and every supported USCRN daily validation
station. Scores are accumulated by regime and then averaged equally across
the six regimes. Validation never calls backward and never changes fit state.

The early-stop improvement epsilon is `1e-4` in the equal-regime primary NLL.
Training runs at least 20 epochs, at most 100, and stops after ten consecutive
non-improving validations. This epsilon, epoch size, and deterministic sampler
are implementation completions frozen prospectively here.

## Model and likelihood completion

Every row uses a width-128 MLP of frozen depth, a single GRU state of frozen
latent width, and distribution heads for precipitation occurrence/positive
amount plus six continuous transformed daily fields. N0 receives transferable
calendar/location descriptors. N1 adds fit-identity embeddings with a
zero-centered L2 hierarchical penalty; unseen validation and generation
identities receive the exact zero deviation. Parameter count includes all
embeddings and must remain at or below 50 million.

The primary score is Bernoulli occurrence NLL plus positive-amount lognormal
or bounded-shape GPD NLL and Gaussian transformed-field NLL, normalized by
valid targets after the 60-day mask. Auxiliary terms and weights are exactly:
wet/dry transition survival 0.05, monthly expected precipitation 0.05, annual
aggregate dispersion 0.04, precipitation-context dependence 0.04, and latent
state/embedding stability 0.02. Their sum is 0.20, below 0.25. Each is divided
by its observed null scale or valid count; an unsupported term contributes
zero and is reported, never fabricated.

AdamW (`lr=0.0003`, weight decay `0.01`), batch 64, deterministic bf16 forward
with fp32 state/loss, and gradient norm 1.0 are exact. Checkpoints publish via
temporary write, fsync, SHA-256 verification, and rename at each epoch and at
most every 15 minutes; only the newest two verified rolling payloads remain.

## Generation and runtime

Each valid fit executes unforced 1/30/100-year generation with Random123
Philox 4x32-10 counter layout `station,burn,member,date,draw`. Positive/range/
probability support comes from declared distribution transforms; no clipping,
repair, or balancing path exists. Non-finite output, bad calendar, non-nested
prefix, batch/order dependence, state instability, or support failure marks
the fit invalid.

The normative CPU benchmark uses the exact M3 six stations, 30/100 years, two
warmups, nine alternating samples, at least one timed second, one pinned core,
and the release faithful binary on the same allocated L40 node with its GPU
hidden. Every valid screen row is benchmarked, which is stronger than the
minimum requirement to benchmark promotion-eligible rows. Ratios are unrounded:
`<5 PASS`, `[5,10) WARN`, `>=10 FAIL`. Absolute cold/load, RSS, export-size,
and per-horizon safeguards are independent hard checks.

## Promotion and resources

Within each pooling class, valid rows sort by
`validation_primary_nll`, `validation_tail_score`, `validation_stability`,
`parameter_count`, then `configuration_id`. Runtime-failing rows remain
published but cannot promote. The first at most two non-failing rows per class
promote to A10M6. M5 does not choose a finalist or read development output.

Each of 12 jobs requests one typed L40, 8 CPUs, 65,536 MiB, and 120 minutes.
The matrix requests 24 GPU-hours plus a five-minute exact-node recovery
reserve, beneath the frozen 160-hour screen ceiling and with concurrency two.
