# A5d1 Selector Feasibility Gate Results

Overall: `PASS`
Date: 2026-07-14 (America/Los_Angeles)
Evidence source commit: `f676a8e6ab09f4e399b27afe57bcd30938bb592f`
Controlling freeze: `dd38484dca7da633ed30854c16074fa66b2a7a7fdd53b05253277125cdd99d22`

## Authority and package gates

| Command or check | Result |
|---|---|
| `python3 .../verify-a5c-decision.py` | PASS; 24 locked files, 14 candidate/horizon rows, zero eligible/promoted profiles, 6/6 mutations rejected |
| `python3 .../verify-a5d0-package.py` | PASS; 19 locked inputs, zero public changes/exposure, 7/7 mutations rejected |
| V6 strict contract/schema validation | PASS; Draft 2020-12 schema, unknown nested members rejected |
| V6 freeze chronology | PASS; 306 unique cells, no v6 outcomes at freeze, v2–v5 invalidations disclosed |
| `python3 artifacts/run-synthetic-fixtures.py` | PASS; 15/15, including aggregate January transition and zero boundary-denominator cases |
| Exposure ledger | PASS; zero confirmation objects, target values/scores, WEPP responses, public candidates, and production/public changes |

## Generation, numerical, and path gates

| Gate | Result |
|---|---|
| Library regeneration | PASS; 17/17 stations, two recorded generations, climate/quality/provenance hashes identical, 112,875,835 retained bytes |
| Feature extraction | PASS; 17/17 256-block station records, 194 common + 62 leap blocks each |
| Marginal solver/certificate replay | PASS; 34/34 reconstructed, 30 pass, pool 256 = 17/17 |
| Frozen matrix | PASS; expected = actual = unique = 306 |
| Aggregate January replay | PASS; all records recompute, 290/306 30-year and 293/306 100-year component passes |
| Complete finite path result | Honest negative result; 0/306 pass, with 36 stationary / 265 finite-prefix / 3 boundary / 2 dependence first failures |
| `python3 artifacts/verify-physical-row-identity.py` | PASS; 306/306 independently rendered, zero physical interventions, exact 30-year prefix |
| `python3 artifacts/archive-detailed-evidence.py` repeat | PASS; deterministic SHA-256 `18c2be90b1d431ca1dd4bf031b274b0413c3363fa0ebf0c01d1580c34cdc73b0`, 340 ordered members |
| `python3 artifacts/verify-a5d1-replay.py` | PASS; 306 structurally identical paths, 141,064 numeric comparisons, 0 mismatches at `2e-10`, maximum absolute difference `3.11e-15` |
| `python3 artifacts/verify-a5d1-closure-supplement.py` | PASS; four resource ceilings, all manifest records, full detailed semantics, and terminal aggregates |
| `python3 artifacts/verify-a5d1-package.py` | PASS; frozen verifier plus closure records and mutation tests |

The replay's exact JSON hashes differ after runtime removal because 255 path
records contain last-bit linear-algebra differences. No structural field or
decision differs, and the largest numeric difference is 3.11e-15, far inside
the frozen numerical replay guard and the closure audit's 2e-10 comparison
tolerance. The replay archive and audit are retained and hash-bound rather than
described as exact-byte identity.

## Resource gates

| Measurement | Observed | Frozen ceiling | Result |
|---|---:|---:|---|
| Retained library storage | 112,875,835 bytes | 1,073,741,824 bytes | PASS |
| Maximum resident set across first execution stages | 400,883,712 bytes | 2,147,483,648 bytes | PASS |
| Maximum marginal station/pool solver time | 0.335521 s | 120 s | PASS |
| First execution stage wall-time upper bound | 592.82 s | 7,200 s | PASS |

The first path execution used 559.19 wall seconds and 206,389,248 maximum
resident bytes. A retained semantic replay used 1,599.82 wall seconds and
185,991,168 maximum resident bytes; it remained below the same ceilings.
`resource-evidence-v1.json` binds commands, exit statuses, exact tool/input
hashes, internal stage metrics, published result metrics, replay evidence, and
all four ceiling decisions.

## Independent review gates

| Lens | Result |
|---|---|
| Accuracy/numerical | ACCEPT after ACC-V6-001/002/003 closure-supplement recheck |
| Scientific validity | ACCEPT after aggregate January design and corrected H3 report recheck |
| Consistency/exposure/public safety | ACCEPT after chronology, schema, archive, physical, exposure, and LFS checks |
| Open findings | PASS; P1 = 0, P2 = 0, P3 = 0 |

## Repository and public-safety gates

| Command or check | Result |
|---|---|
| `cargo fmt --check` | PASS |
| `cargo clippy --all-targets -- -D warnings` | PASS |
| `cargo test` | PASS; faithful byte-parity tests included |
| `git diff --check` | PASS |
| Local Markdown links and catalog/status consistency | PASS |
| Strict JSON parse and duplicate/nonfinite mutation tests | PASS |
| `git check-attr` for retained evidence archives | PASS; current, invalidated-v4, and replay archives use `filter=lfs` |
| Staged Git objects | PASS; all three retained archives are LFS pointer blobs |
| `git lfs fsck` | PASS |
| `git ls-files references/copyrighted | wc -l` | PASS; 0 tracked files |
| Credential, absolute operator path, confirmation/public-candidate scan | PASS |

Coverage and CRAP gates do not apply: no production function under `crates/`
changed.
