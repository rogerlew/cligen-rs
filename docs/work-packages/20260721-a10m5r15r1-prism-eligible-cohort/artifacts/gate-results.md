# Gate results

- Frozen queue: PASS — 72 prospective points, no climate-value ordering.
- Acquisition: PASS — 36 requests, 36 accepted; cold 8, hot-arid 28.
- Final selection: PASS — 1,440 unique points; exact 200/40 per regime.
- Leakage: PASS — no cross-role point/tile and no protected role opened.
- Calendar: PASS — all 1,440 records have 10,950 source rows on the canonical
  10,958-row Gregorian axis.
- PRISM coverage: PASS — all 1,440 corpus and six temporal containing cells.
- Normalization: PASS — 1,200 candidate-fit points only; 36 finite nonzero
  population scales.
- Transfer: PASS — 60 Daymet + 38 inherited USCRN objects; all hashes and
  223,729,862 aggregate bytes verified.
- `python3 artifacts/verify_scaffold.py`: PASS.
- `python3 artifacts/verify_cohort.py`: PASS.
- `cargo fmt --check`: PASS.
- `cargo clippy --all-targets -- -D warnings`: PASS.
- `cargo test`: PASS.
- `git diff --check`: PASS.

No production function under `crates/` changed, so the coverage/CRAP gate does
not apply.
