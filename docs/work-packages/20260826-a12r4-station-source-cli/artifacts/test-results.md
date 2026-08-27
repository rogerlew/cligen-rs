# A12R4 test results

Status: PASS

Source commit: `1e558b553412bfdc0f1b61ccd5c331ced056de54`

Release binary SHA-256:
`a6491ed5e4b39dc52ae8fc2426cb7eef5a8fa1ee37e20bfc48df55c73ec7bac0`.

## Repository gates

- `cargo fmt --check`: PASS
- `cargo clippy --all-targets -- -D warnings`: PASS
- `cargo test`: PASS, including 52 library tests and all workspace integration
  suites; registered long-running local-capture tests remained explicitly
  ignored as before.
- `cargo llvm-cov --workspace --lcov --output-path target/lcov.info`: PASS;
  LCOV SHA-256
  `d3dba4d22c08d1e1abdae49101b759eccc08f3b05ba389ade6865a7f3faf6c59`.
- `cargo crap --workspace --lcov target/lcov.info --exclude 'tests/**'
  --fail-above`: PASS; 861 functions analyzed, zero above CRAP 30.

## Focused and end-to-end evidence

Unit coverage includes all five method IDs, CLI conflicts and elevation
validation, ten-candidate feasibility filtering, no-eligible failure, full
source-model finite/domain preflight, exact-ID zero/duplicate bytewise lookup,
exact-file lexical/canonical paths, and mutation after the one-time read.

The hash-pinned release binary executed default plus replay, both optional
heuristics, exact ID, exact file, exact-file symlink, dry-site default with and
without repair, and exact dry-site repair. Every successful run published 11
artifacts whose manifest hashes were independently recomputed. Every selection
receipt's executable hash matched the release binary and top-level manifest;
every source hash matched `source-station.par`.

Default and replay request, method, normals, selection, source/localized `.par`,
localization, runspec, and climate bytes were identical. At the dry point, both
automatic runs chose `ca043914.par` with the same four rejections and the repair
run made zero repairs. Exact `ca040983.par` failed ordinarily and succeeded only
with the explicit method, warning for and recording one repair in month 6.

Missing ID, ordinary-unlocalizable exact ID, dangling symlink, directory-valued
`.par`, and missing elevation target all exited 1 and published no destination.
Full hashes and assertions are in `runtime-evidence-v1.json`.
Its SHA-256 is
`7ab1aa790063469565c25547ef462b64e7172e804061716f495ba5120ad54fc5`.
