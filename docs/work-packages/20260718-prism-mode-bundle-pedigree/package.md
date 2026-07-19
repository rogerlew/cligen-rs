# PRISM Mode Bundle, Pedigree, and Limitations

Status: `FROZEN-EXECUTION`
Date: 2026-07-18
Evidence mode: Mixed primary-source review, source history, and ran validation
Starting branch and push target: `main`, push `main`

## Objective

Close the public Cargo PRISM mode as a self-describing operational surface:
retain the already-published hash-pinned runtime and exact-source bundles,
record its FSWEPP/Rock:Clime origin and later published/implementation lineage,
freeze its differences from WEPPcloud, and emit its limitations with every
generated artifact set.

## Scope

Included:

- the existing `cligen prism sync | query | run` command surface and published
  `prism-normals-2026.07` runtime/source assets;
- a strict, versioned method record embedded in the Cargo binary and emitted
  as `method.json` by every successful `prism run`;
- FSWEPP/Rock:Clime, Brooks et al. (2016), source-pinned `wepppy`, and
  cligen-rs lineage with non-authority boundaries;
- a frozen behavior/difference matrix and explicit scientific limitations;
- specification revision 3 and user documentation; and
- exact repeatability, manifest inclusion, repository gates, coverage, and
  CRAP validation.

Excluded:

- any change to station selection, localization equations, thresholds,
  fixed-width rendering, PRISM values, bundle bytes, faithful generation,
  RNG, or existing profile identity;
- a claim that FSWEPP, Brooks et al., WEPPcloud, and cligen-rs implement the
  same algorithm; and
- a claim that the mode is observed daily/subdaily truth or has passed a
  general climate-quality standard.

## Authority

- FSWEPP Rock:Clime documentation establishes the original USDA Forest
  Service PRISM-assisted custom-CLIGEN climate concept and station database.
- Brooks et al. (2016), DOI `10.1016/j.jhydrol.2015.12.004`, is published
  evidence of monthly PRISM precipitation/Tmax/Tmin climate spatialization for
  WEPP, but is not authority for this `.par` algorithm.
- `wepppy` commit `3ee74d02df445a30968ef92975e5e3e2f6084669` and exact file SHA-256
  `4071cc72165d174851316349c0d96a3f4fa06fcf0b2d91e5b67de439f39a42c1`
  establish the reviewed automated implementation lineage.
- SPEC-A10-STOCHASTIC-PRISM-COMPARATOR revision 3 is the cligen-rs behavior
  authority. The faithful generator remains governed by the vendored Fortran.

## Plan

1. Freeze primary sources, local source identities, and the behavior matrix.
2. Publish the versioned method-record contract with the specification before
   changing production output.
3. Embed and emit the record without changing climate behavior; bind it into
   the existing top-level artifact manifest.
4. Validate bundle availability, method output, exact repeatability, all
   repository gates, coverage, and CRAP.
5. Close the package and reconcile the catalog and roadmap.

## Gates

- `method.json` exactly matches the embedded registered record and is included
  by hash in `artifact-manifest.json`;
- the record identifies FSWEPP/Rock:Clime as origin, distinguishes Brooks et
  al. and WEPPcloud lineage, and carries every registered limitation;
- a before/after climate-behavior check proves the change is provenance-only;
- both registered release assets remain byte/size identified and accessible;
- `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, and
  `cargo test` pass; and
- workspace llvm-cov and CRAP gates pass with no production function above 30.

## Exit criteria

`PRISM-MODE-BUNDLE-PEDIGREE-READY` requires the complete machine-readable and
human-readable pedigree/limitation surface, unchanged climate behavior,
verified published bundle identities, and all gates green. A bundle identity
failure, unresolvable pedigree conflict, artifact-schema defect, or behavior
change closes with a typed hold and exact evidence.

## Artifacts

- `artifacts/design-freeze.md` — immutable scope and claim boundary;
- `artifacts/pedigree-sources.md` — primary documents and source-history
  findings;
- `artifacts/behavior-matrix.md` — frozen implementation comparison;
- `artifacts/method-record-contract.json` — exact public record;
- `artifacts/verify.py` — package verifier; and
- `artifacts/gate-results.md` — executed validation record.
