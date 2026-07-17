# A10M1 gate results

Date: 2026-07-17
Terminal: `A10M1-CORPUS-READY`

## Package-specific gates

| Gate | Evidence | Result |
|---|---|---|
| six-regime Daymet fit/validation coverage | 200/40 locations in each regime; 351 final tiles | PASS |
| tile and station role isolation | zero tile splits, station splits, or confirmation overlap | PASS |
| protected-site distance | minimum 100.005749 km against 100 km boundary | PASS |
| current USCRN inventory | 255 rows inventoried; 24 eligible used according to availability | PASS |
| actual event frequencies | 14 stations; 21,495 events; no floor/substitution | PASS |
| calendar transform | synthetic vectors plus observed 10,950/10,958 row mask audit | PASS |
| missingness/units | field glossary; 69,693 availability-cube rows; null masks | PASS |
| fit-only normalization | 152 `candidate_fit` statistic rows | PASS |
| inherited development integrity | 32/32 accepted A9 object hashes | PASS |
| confirmation firewall | target access false; no overlap or target-byte hash | PASS |
| source rights | Daymet/USCRN permitted; PRISM/gridMET not acquired | PASS |
| transfer integrity | 98/98 hashes; 223,799,545 bytes | PASS |
| historical v1 auditability | 60/60 v1 plus 60/60 v2 shard hashes | PASS |
| resource ceilings | <4.7 GiB conservative download; 1,177,616 KiB local retained; no GPU | PASS |

## Executed commands

```text
git diff --check
python3 -m py_compile .../a10m1_corpus.py
python3 .../a10m1_corpus.py verify
python3 <JSON parse of 16 package/specification artifacts>
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
git diff --name-only 936a5c4 -- crates
```

Results: all pass. `cargo test` ran with host loopback access because two
station-network tests bind local HTTP fixture sockets; the restricted first
run failed only those binds with `Operation not permitted`, and the unchanged
host-context rerun passed the complete suite. The `crates/` diff is empty, so
no production function changed and the coverage/CRAP gate is not triggered.

The final executable verifier printed:

```text
PASS self-test: calendar, 0000 boundary, and 72-zero event separator
PASS verify: six regimes, 98 transfer objects, zero confirmation access
```
