# Gate results

- Prospective freeze verifier: PASS.
- Science dependency identity verifier: PASS (12/12 identities).
- Admission checker self-tests: PASS (6/6).
- Operational identity self-tests: PASS (6/6).
- Full calendar/missingness preflight: PASS and byte-identical to R0.
- Staging and staged asset verification: PASS.
- Control submission admission: PASS (15/15 gates).
- Control execution: HOLD before runtime extraction; host Python 3.6 rejected
  the Python 3.11 diagnostics source.
- Candidate fail-closed admission enforcement: PASS (10/10 rejected before
  runtime extraction).
- Job-local cleanup: PASS (11/11).
- Remote cleanup: PASS; exact owner-bound root independently absent.
- Portfolio science/selector: NOT RUN and not interpretable.
- Toolkit collection/close: HOLD because the evidence allowlist cannot express
  absent PASS-only receipts for rejected roles.
- Post-run record reconciliation: `python3 -m unittest
  research.a10.lemhi_toolkit.tests.test_hardening
  research.a10.lemhi_toolkit.tests.test_toolkit` PASS (79 tests), remote packer
  shell syntax PASS, `git diff --check` PASS, `cargo fmt --check` PASS,
  `cargo clippy --all-targets -- -D warnings` PASS, and `cargo test` PASS.
