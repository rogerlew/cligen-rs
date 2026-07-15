# A8c1 release-exposure audit

Status: `REMOVAL-SUPPORTED`  
Audited: 2026-07-15  
Repository: `rogerlew/cligen-rs`  
Dispatch commit: `49a67775d22f0452bbf65f0a1ad35435e0d340f9`

## Decision

No published crate, tag, or release contains the A8c runtime. Direct removal
from current `main` is supported; a deprecation shim is not required.

## crates.io evidence

- The official sparse-index object
  [`https://index.crates.io/cl/ig/cligen`](https://index.crates.io/cl/ig/cligen)
  returned HTTP 404 `NoSuchKey` on 2026-07-15.
- `cargo search cligen --limit 100` returned zero rows on the same host and
  date.
- The crates.io API endpoint returned HTTP 403 under the registry's data-access
  policy rather than a crate record. The audit does not interpret that response
  as absence; the independent sparse-index 404 and Cargo search establish the
  registry result.
- Workspace metadata reports package `cligen` version `0.1.0`, repository
  `https://github.com/rogerlew/cligen-rs`, and no `publish = false` field. This
  is local package metadata, not publication evidence.

## GitHub release and tag evidence

The official [release list](https://github.com/rogerlew/cligen-rs/releases) and
authenticated GitHub API expose exactly two releases/tags:

| Tag | Commit | Published UTC | Purpose |
|---|---|---|---|
| `station-db-2026.07` | `927f03e6ce8ef504b964f31ed72884e53dbd6f9c` | 2026-07-10 20:25:43 | station collection payloads |
| `q3-evidence-2026.07` | `a5e3caca1430b656b6358f5277900c108ce36cb7` | 2026-07-10 23:38:49 | Q3 evidence archive |

The A8c implementation first appears in
`fdd35f60241f25663614db46142bfe3683c6ce5f`, committed on
2026-07-15 20:09:15 UTC. Neither tag contains that commit, and
`git tag --contains fdd35f6` returns no tag. Both release commits predate A8c.

## Source-history evidence

- Pre-A8c comparator:
  `046eba3c8d4508c84522c6dbd7cec4d39f094563`.
- A8c implementation/evidence commit:
  `fdd35f60241f25663614db46142bfe3683c6ce5f`.
- A8c1 scaffold/dispatch commit:
  `49a67775d22f0452bbf65f0a1ad35435e0d340f9`.
- Git history remains the compatibility path for an exact dependency on the
  stopped implementation.

The hash-bound pre-removal inventory is
[`a8c1-baseline-v1.json`](a8c1-baseline-v1.json), SHA-256
`4ae8e8084182c2ba32675d73a018b3ab383dcf72bf66ba79fc0585441b5eb56e`.
It covers 27 removal surfaces, 148 preserved files, and four mutable retirement
status documents.

## Conclusion

The A8c station-document revision, station model, generation profile, and
runtime were committed to `main` but never shipped through crates.io or a
repository release/tag. Under the A5f1 retirement precedent and the A8c1
contract, removal is the correct compatibility disposition.
