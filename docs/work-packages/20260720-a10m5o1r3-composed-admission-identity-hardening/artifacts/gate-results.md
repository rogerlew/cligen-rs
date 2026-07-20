# Gate results

Date: 2026-07-20

## Toolkit and contract

- `python3 -m unittest discover -s research/a10/lemhi_toolkit/tests -v`:
  PASS, 86 tests.
- `python3 -m py_compile research/a10/lemhi_toolkit/core.py
  research/a10/lemhi_toolkit/tests/test_hardening.py`: PASS.
- all 20 `research/a10/lemhi_toolkit/remote/*.sh` files under `sh -n`: PASS.
- every JSON artifact in this package parsed with Python's standard JSON
  parser: PASS.
- `git diff --check`: PASS.

The adverse fixtures cover missing, extra, reordered, wrong-hash, malformed,
locally changed, prepared-state-changed, and transfer-record-changed checker
identities. They also cover stale or ambiguous semantic-plan revisions,
unpromoted/non-revalidated transfer state, and empty, duplicate, unsafe, missing,
non-repository-owned, non-executable, materializer-aliased, and unknown-protocol
plan chains; missing, symlinked, and outside-authority receipt directories; and
post-verification admission-contract amendment. Every submit-path rejection
asserts zero attempts, a genesis-only ledger, and zero adapter submissions.

## Repository gates

- `cargo fmt --check`: PASS.
- `cargo clippy --all-targets -- -D warnings`: PASS.
- `cargo test`: PASS.

Coverage/CRAP was not triggered because no production function under `crates/`
changed. No HPC allocation, remote mutation, or scheduler reservation was used.
