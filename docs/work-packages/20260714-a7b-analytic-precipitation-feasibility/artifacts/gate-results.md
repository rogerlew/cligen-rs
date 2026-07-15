# A7b gate results

Status: `ACCEPTED-WITH-SCOPE-CORRECTION`
Date: 2026-07-14
Source commit: `3e18728b4c63c17be922e98199948c1b7da8002e`
Terminal decision: `STOP-PRECIPITATION-LINE`

## Pre-analysis boundary

Commands:

```sh
python3 -m py_compile docs/work-packages/20260714-a7b-analytic-precipitation-feasibility/artifacts/{analyze,verify,freeze}-a7b.py
python3 docs/work-packages/20260714-a7b-analytic-precipitation-feasibility/artifacts/analyze-a7b.py --synthetic-check
python3 docs/work-packages/20260714-a7b-analytic-precipitation-feasibility/artifacts/freeze-a7b.py
```

Result: PASS before candidate-specific output. Synthetic stationary-kernel
checks passed and the first freeze bound methods, parent inputs, and unchanged
production sources. The first authoritative invocation then stopped at the
A7a terminal-key check before candidate-data access. Amendment 001 records the
bounded `terminal` → `terminal_decision` correction, original and amended
analyzer identities, and the absence of outcome artifacts; the amended freeze
binds that record. No candidate, threshold, estimator, or decision rule
changed.

## Package-specific evidence gates

Commands:

```sh
python3 docs/work-packages/20260714-a7b-analytic-precipitation-feasibility/artifacts/analyze-a7b.py
python3 docs/work-packages/20260714-a7b-analytic-precipitation-feasibility/artifacts/verify-a7b.py --reproduce
python3 docs/work-packages/20260714-a7b-analytic-precipitation-feasibility/artifacts/verify-a7b.py
python3 docs/work-packages/20260714-a7b-analytic-precipitation-feasibility/artifacts/verify-equivalence.py
```

Result: PASS. The authoritative run returned
`STOP-PRECIPITATION-LINE`. The separate verifier checked all freeze and input
identities; source ancestry and unchanged production crates; 17 stations, 68
amount fits, 136 occurrence fits, 408 candidate-month cells, and 34 likelihood
records; every stationary kernel; and every feasible cell's finite-window
occurrence moments, amount quadrature, variance budget, probability, tail, and
retention bounds. It independently recomputed summaries and the terminal,
then reproduced analysis, decision, and findings byte-for-byte.

Canonical identities:

- contract: `21e3ff616683aab15eeb41b233a78ba29f428161212e44bdfffbf201006470f3`;
- amended freeze: `58c324fd9b86ebecf046a1591fd3ef9cc663cd713146721bf983a36bd76141bc`;
- amendment 001: `7adce3319f4185d0fd5e998df8fc5c6032dbb1df6d2f6a133fd556c84a10f1b3`;
- analysis: `f460055a7978932747ed0bb969d89917c00067af7500f3d0fd833d7af1321d3b`;
- decision: `263a0e6788afcc7a49b07be9879ddabbc58adbe3188a73145c2f06b861a778a8`;
- findings: `93a8d1b8c09a064eca565de8ae115794d370e2bb4f4c998a05356dc5902e5eeb`;
- equivalence review:
  `d8b376b3d83adbfc49f8ec0cd7a84d37e4ac3dc635e850b9876a3fa32af00fa7`;
- consolidated review:
  `636f6657c45cbfb8feb8577f02faa2292c596f7ddd2ad0d87adbfdc46381e234`.

## Scientific and consistency review gates

- Accuracy: ACCEPT. Independent matrix and quadrature recomputation and
  byte-for-byte reproduction passed.
- Scientific validity: ACCEPT WITH SCOPE CORRECTION. Review proved that the
  two registered occurrence candidates are isomorphic parameterizations of
  one four-state process. Both have the same infeasible cells, so the stop is
  invariant; the work does not claim comparison of two independent classes.
- Prospective restraint: ACCEPT. No threshold relaxation, station replacement,
  data pooling, near-miss selection, or A7c dispatch followed the 31/36
  development result.
- Consistency/public safety: ACCEPT. Parent/source identities and public links
  are local and stable; no operator-specific absolute path or copyrighted
  reading-copy reference is present.
- Consolidated review: zero open P1 and zero open P2 findings.

## Repository gates

Commands:

```sh
git diff --check
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
```

Result: PASS. The workspace test command completed with 192 passed, zero
failed, and nine expected evidence/environment-dependent tests ignored.

Coverage and CRAP gates are not applicable because A7b changes no production
function under `crates/`.

## Storage gate

Command:

```sh
git check-attr filter -- docs/work-packages/20260714-a7b-analytic-precipitation-feasibility/artifacts/a7b-analysis-v1.json
```

Result: `filter: unspecified`. The canonical analysis is approximately 1.1 MB,
textual, and intentionally retained as ordinary diffable Git content; LFS is
not appropriate for this artifact.
