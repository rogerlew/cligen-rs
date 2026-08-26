# A11E4 test results

Date: 2026-08-25

## Prospective source gates

- Bundled Python 3.12.13 / NumPy 2.3.5 synthetic suite: PASS, 15 tests.
- Strict manifest/schema validation: PASS; canonical digest
  `358ff235f70aa69b7216419e8864e06c312a84457dbc08df5e8997381442f666`.
- `cargo fmt --check`: PASS.
- `cargo clippy --all-targets -- -D warnings`: PASS.
- `cargo test`: PASS (repository-declared ignored evidence tests remain ignored).
- `git diff --check`: PASS.
- Independent corrected-source review: GO, no unresolved P0/P1.

## Execution and replay gates

- Published source: `dfef66cac102bdcd9f9ab8e163bd0e088e20e5b0`.
- First execution: PASS in `3.6097444999977597` seconds.
- Authorized replay: PASS in `3.594386167002085` seconds.
- Scientific evidence replay SHA-256:
  `6622309dc9410ae778c67963160c7abef7c61730442118f427b7ea4f0e7f5dad`.
- Decision replay SHA-256:
  `d5c1401516299516a3578ae4c08d32e368f2746db2a22c173925f4376171be67`.
- Evidence canonical self-hash:
  `66f08b7aee18da217874062e3779cfa27e67c81be1e31a2ce271cf9631e5c35f`.
- Exact grid/join and inference: PASS; 20 stations, eight members,
  1,327,104 assignments, zero degenerate assignments, identity counted.
- Confirmation target access: false.
- Terminal decision: `NO_STABLE_METADATA_ASSOCIATION`.
- Independent completed-evidence review: GO; all arithmetic, hashes, stability
  checks, disposition, and stop rules reproduced with no remaining P0/P1.
- Final synthetic suite and manifest validation: PASS, 15 tests and canonical
  digest unchanged.
- Final repository gates: PASS (`cargo fmt --check`,
  `cargo clippy --all-targets -- -D warnings`, and `cargo test`).
- `git diff --check` and changed-document relative links: PASS.
