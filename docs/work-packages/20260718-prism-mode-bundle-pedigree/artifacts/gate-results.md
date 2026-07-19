# Gate results

Executed 2026-07-18 on `main`.

## Method contract and output binding

- `python3 artifacts/verify.py` passed with
  `PRISM-METHOD-CONTRACT-VERIFIED`
  `2c6668828292cb95c167fea4249eff89762901deba03c702bff0d26036c18924`.
- A corrected release build wrote `method.json` byte-identically to the
  embedded record: 3,030 bytes and the same SHA-256.
- `artifact-manifest.json` enumerated `method.json` with that exact byte count
  and hash.
- The method record has the three ordered pedigree stages FSWEPP Rock:Clime,
  WEPPcloud `wepppy`, and cligen-rs, plus all nine registered limitations.

## Provenance-only behavior check

The pre-change and corrected post-change release binaries each ran the same
one-year request at longitude -117.0 and latitude 46.73 against the same local
data root. Exact `cmp` passed for:

- `climate.cli`;
- `localized.par`;
- `prism-normals.json`;
- `station-selection.json`; and
- `localization.json`.

Both `climate.cli` files have SHA-256
`821106826315f4c89a055dca15b20cb6b3526d8697d2cbadfb265de75d6ad120`.
The changed mode therefore adds provenance visibility without changing its
climate, localization, or selection behavior.

## Published bundle

GitHub release `prism-normals-2026.07` was queried during execution and was
neither a draft nor a prerelease. Both assets were downloaded afresh and
matched the embedded distribution record:

| Asset | Release asset | Bytes | SHA-256 |
|---|---:|---:|---|
| Runtime | 481957711 | 62,509,110 | `49fe87c83511678094e1033ecc2143d5d833811135934858aab854af78c28292` |
| Exact source | 481957709 | 108,213,469 | `c3b832d43de54face39486673843d6c5bc511793804f5678dcb1af809ac0475c` |

A fresh air-gap sync and network-free query at longitude -117.0, latitude
46.73 passed. The query selected row 76, column 192 and returned 12 values for
each of monthly precipitation, Tmax, and Tmin. An initial audit assertion
expected an obsolete nested receipt shape after the query itself succeeded;
the assertion was corrected to the registered flat receipt and passed
`PRISM-AIRGAP-QUERY-READY`. This was an audit-script expectation correction,
not a product failure.

## Repository gates

- `cargo fmt --check`: passed.
- `cargo clippy --all-targets -- -D warnings`: passed.
- `cargo test`: passed. A first logging wrapper subsequently tripped over
  zsh's reserved `status` variable after Cargo had completed successfully; the
  recorded rerun used `gate_rc` and passed normally.
- `cargo llvm-cov --workspace --lcov --output-path target/lcov.info`: passed.
- `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**'
  --fail-above`: passed; 826 functions analyzed, zero above CRAP 30.
- `git diff --check`: passed.
- Attribution search over the public and package surfaces found no reference
  to the operator-corrected unrelated publication branch.

All package gates are green.
