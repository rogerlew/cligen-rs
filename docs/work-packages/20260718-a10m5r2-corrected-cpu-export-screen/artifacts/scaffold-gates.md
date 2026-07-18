# A10M5R2 scaffold gates

Prospective verification before allocation: `PASS`.

- Python AST and generated-wrapper finalizer parse;
- byte-exact A10M5 trainer-core staging;
- twelve complete predecessor identity sets;
- explicit trainer-exit/fresh-worker process boundary;
- `/proc` `VmRSS`/`VmHWM` and external `/usr/bin/time -v` surfaces;
- frozen grid, seed, resources, and protected-role boundary;
- repository formatting, clippy, and test gates.

Commands passed on `rmm`:

```text
python3 artifacts/verify.py
python3 -m unittest research.a10.lemhi_toolkit.tests.test_toolkit research.a10.lemhi_toolkit.tests.test_hardening
sh -n artifacts/jobs/screen-job.sh
git diff --check
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
```

The verifier constructed all twelve wrappers from the canonical cache in a
temporary directory, parsed every embedded finalizer, matched the staged
trainer core byte-for-byte with A10M5, and found twelve complete predecessor
identity sets. No remote command or allocation occurred.
