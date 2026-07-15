# A5f1 Release-Exposure Audit

Status: `REMOVE-UNSHIPPED-RUNTIME`
Observed: 2026-07-14 America/Los_Angeles
Source commit: `9eada9229606667ff083f69fe968364dead31d10`

## Official Rust registry

- `https://crates.io/api/v1/crates/cligen` returned HTTP 404 with
  `crate 'cligen' does not exist`.
- `https://index.crates.io/cl/ig/cligen`, the exact sparse-index key for the
  crate name, returned HTTP 404/`NoSuchKey`.
- `cargo search cligen --registry crates-io --limit 100` returned no exact
  registry entry.
- `cargo info cligen` resolved only the local workspace package and identified
  version `0.1.0`; it did not retrieve a registry package.

## Repository releases and history

`gh release list` reported only:

- `station-db-2026.07`, commit `927f03e6`, 2026-07-10; and
- `q3-evidence-2026.07`, commit `a5e3caca`, 2026-07-10.

Both precede the first A5e0 implementation commit,
`1ca40bbe006ed5d823d2dd8e373f720f20d60ba0` on 2026-07-14. Neither is a Rust
crate release. No repository tag or GitHub release contains A5e0.

## Decision

The source repository is public, so an unrecorded Git dependency is possible,
but no versioned crate or release contract contains `cligen::a5e0`. The exact
historical commit remains available for such consumers and for scientific
reproduction. A deprecation shim would keep more than 1,100 lines of a retired
experimental mechanism in every build without protecting a shipped semver
surface. A5f1 therefore removes the current runtime and preserves the history.
