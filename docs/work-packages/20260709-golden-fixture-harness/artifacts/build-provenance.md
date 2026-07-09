# Reference Build Provenance

Evidence mode: Ran
Date: 2026-07-09

## Source

- Source directory: `reference/cligen532/`
- Directory digest command:
  `find reference/cligen532 -maxdepth 1 -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum`
- Directory digest: `24966eaed920c2b9fd0b8a9ab1242b32053a730f0691a6a18dc4f44a3096bd5b`
- `cligen.f` SHA-256: `3dfd51db98fedfbfb155d4227099cf9133043d4d699093268ed21ce16ec4267c`
- Individual source hashes are in the command transcript and can be
  regenerated with `sha256sum reference/cligen532/cligen.f reference/cligen532/*.inc reference/cligen532/makefile | sort`.

`reference/cligen532/` was not modified.

## Compiler

Command:

```sh
gfortran -O0 -ffp-contract=off -fprotect-parens -fno-fast-math \
  -Ireference/cligen532 reference/cligen532/cligen.f \
  -o docs/work-packages/20260709-golden-fixture-harness/artifacts/build-run-a/cligen532-pinned
```

Compiler:

```text
GNU Fortran (Homebrew GCC 14.2.0_1) 14.2.0
```

Fixture profile decision:

- `-O0`: chosen for conservative golden generation.
- `-ffp-contract=off`: FMA contraction disabled.
- `-fprotect-parens`: explicit parenthesis protection.
- `-fno-fast-math`: explicit fast-math-family rejection.
- The vendored `reference/cligen532/makefile` optimized target remains
  disqualified for fixture generation because it enables expression
  reordering / fast-math-family flags.

Build logs:

- `artifacts/logs/build-run-a.log`
- `artifacts/logs/build-run-b.log`

The logs contain only legacy Fortran warnings (`ASSIGN`, assigned `GOTO`,
arithmetic `IF`, shared DO termination labels).

## Binaries

Two independent builds were produced for the determinism self-gate.

| Build | Path | SHA-256 | Size | Mtime |
|---|---|---|---:|---|
| A | `artifacts/build-run-a/cligen532-pinned` | `cba3a7344d575295ec38dca2f75789ece92137d42712b12223765ce1e1885dde` | 169936 | 2026-07-09 13:42:20.535245083 -0700 |
| B | `artifacts/build-run-b/cligen532-pinned` | `cba3a7344d575295ec38dca2f75789ece92137d42712b12223765ce1e1885dde` | 169936 | 2026-07-09 13:42:22.807289941 -0700 |

## Linked Libraries

`ldd artifacts/build-run-a/cligen532-pinned`:

```text
libgfortran.so.5 => /home/linuxbrew/.linuxbrew/lib/gcc/current/libgfortran.so.5
libm.so.6 => /lib/x86_64-linux-gnu/libm.so.6
libgcc_s.so.1 => /home/linuxbrew/.linuxbrew/lib/gcc/current/libgcc_s.so.1
libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6
```

Library hashes:

| Library | SHA-256 |
|---|---|
| `/lib/x86_64-linux-gnu/libm.so.6` | `1b87a1a50b496cfead2b0ad134c2ff536705c82608db240c7e8aa48d6c0e4217` |
| `/home/linuxbrew/.linuxbrew/lib/gcc/current/libgfortran.so.5` | `d026a3f4d4d5c71cd58de077a81260dc87cf29aaef8dc659d4a3bf09530c1470` |
| `/home/linuxbrew/.linuxbrew/lib/gcc/current/libgcc_s.so.1` | `e2746581ed9da12aa0d4e8064292c77d85e2a108c6a5d9d1c49db193d05162aa` |
| `/lib/x86_64-linux-gnu/libc.so.6` | `d8db8739a1633c972cec6a4fe0566bdcec6fd088f98723492ab0361f66238f75` |

Host libc report:

```text
ldd (Ubuntu GLIBC 2.39-0ubuntu8.7) 2.39
```

## Decisions

Libm pinning:

- The reference binary dynamically links glibc `libm.so.6`, recorded
  above.
- Rust faithful-mode transcendentals remain pinned to the Rust `libm`
  crate per ADR-0001 and the scientific coding standard. This package does
  not change that decision; it records the reference-side libm identity so
  future fixture comparisons know exactly what generated these goldens.

Interior taps:

- Decision: defer deviate-stream / interior trajectory taps to the
  RNG+deviates work package.
- Rationale: this package makes faithful mode falsifiable at the `.cli`
  surface and provides the first-divergent-day/field differ. The
  bit-identity RNG/deviates package is the first package that needs
  internal taps as an acceptance gate, so it should own the recorded tap
  patch and its exact tap schema.
- Constraint carried forward: any tap patch must live under its owning
  work package's `artifacts/` and be applied to a copied build tree, never
  to `reference/cligen532/`.
