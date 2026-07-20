# Scaffold review

Disposition: `ACCEPT — A10M5R14R2R2-SCAFFOLD-READY-FOR-PUBLICATION`

The exact reconstructed child tree differs from R14R2R1 in twelve operational
assets: the composed admission wrapper, inherited operational identities, two
job wrappers, builder, materializer, capacity contract, role map, launcher,
replay identities, setup diagnostics, and selector identities. Candidate code,
objectives, temporal metrics, calendar controls, parameter accounting, corpus,
runtime, and all other frozen science assets are byte-identical.

Focused tests prove the exact two-wave role map, two-device launcher transform,
four-child accounting, and occupancy behavior. A synthetic one-active-GPU
snapshot passes the at-least-two-idle gate; a three-active-GPU snapshot fails.
The generated 51-asset tree compiles and all shell assets parse.

Repository formatting, clippy with warnings denied, the complete Rust suite,
all 86 toolkit tests, four focused package tests, Python compilation, JSON
parsing, shell syntax, and `git diff --check` pass. No production function under
`crates/` changes, so coverage/CRAP is not triggered.

The prepublication tree is evidence only. Execution must regenerate from exact
published `main` and validate the fresh 515-minute authority and two-role plan.
