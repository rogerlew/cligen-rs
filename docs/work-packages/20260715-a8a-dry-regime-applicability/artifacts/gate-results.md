# A8a gate results

Date: 2026-07-15

Terminal: `CONTINUE-A8B-DRY-PARTITION`

## Prospective and source gates

- Metadata-only inventory: PASS — 2,765 stations; catalog SHA-256
  `650b59d17adfdeeab00c5346b812d1d5db791978897c2851ce95c24c133a7211`.
- Selection reproduction: PASS — inventory, 20-station panel, and selected
  parameter archive reproduced byte identically before daily-source access.
- Initial freeze: PASS — SHA-256
  `dd22e50d90db1c49cafa53ad3d54d0fdee486fe7f67e3227685a5881cb9031d5`.
- Bounded source-parser amendment: PASS — amendment 001 records GHCN
  station-list metadata access, zero station daily archives, and zero outcome
  artifacts; successor freeze SHA-256
  `6a1ea6123715cfe2c02aad233e0668792fcf81688de1fe931b6157695cb73656`.
- Primary source completeness: PASS — 20/20 Daymet series, each with 16,790
  fixed-window no-leap records for 1980--2025.
- GHCN sensitivity boundary: PASS — three exact U.S. Cooperative identifiers
  available, two meeting the frozen 90% coverage rule; no substitution.
- Offline source-manifest reproduction: PASS — SHA-256
  `b7e1e31b619b15aff5c153f2724403fee8b63149b0d70d664ca9614fa9e167ae`
  before and after offline verification.
- LFS routing: PASS — all 24 archived `.gz` files resolve to `filter: lfs`
  through `.gitattributes`.

## Analysis and review gates

- Canonical execution: PASS — 28 full station records, 336 monthly analytic
  cells, 80 shortened windows, and the fixed 1,000-replicate bootstrap.
- Analysis SHA-256:
  `78b9b9bb5cd5172459bfb27ba13f7b20ca2cec5af19cab9547c425c7a6e6e89b`.
- Decision SHA-256:
  `1299b6db479c6e57519e5a863183fe49966b75a317850c14e0945f49a211eb58`.
- Independent verification and exact output reproduction:
  `python3 artifacts/verify-a8a.py --reproduce` — PASS.
- Terminal guards: PASS — 8/8 true; 15 integrated and five fallback
  confirmation stations; shortened-window agreement 0.850; monsoonal and
  other-dry instability both 0.1875.
- Consolidated review: ACCEPT — zero open P1/P2 findings; four bounded P3
  observations retained in `review.md`.

## Repository gates

- `cargo fmt --check` — PASS.
- `cargo clippy --all-targets -- -D warnings` — PASS.
- `cargo test` — PASS; 192 passed, 10 ignored, zero failed.
- `git diff --check` — PASS.

Coverage and CRAP gates are not applicable: A8a changes no production function
under `crates/`.
