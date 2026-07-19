# PRISM Residual-Attribution Audit

Status: `SCAFFOLDED`
Date: 2026-07-18
Evidence mode: Mixed static and ran audit
Starting branch and push target: `main`, push `main`

## Objective

Prove that the operator-corrected unrelated publication branch is absent from
every current public PRISM comparator authority and distributable artifact,
while preserving the normal forward-only git correction record. Add a
repeatable fail-closed audit so later documentation or packaging changes
cannot silently restore that attribution.

## Scope

Included:

- the embedded and work-package copies of the PRISM method record;
- README, specification, roadmap, PRISM source, comparator package, and bundle
  package surfaces;
- the exact files selected by `cargo package -p cligen`;
- a newly generated `prism run` artifact set and its manifest;
- attribution-bearing files in both published PRISM release assets;
- the superseded/correcting commit relationship; and
- a fingerprint-based regression verifier that does not reproduce the
  corrected-away name or publication identifier.

Excluded:

- rewriting or force-pushing git history;
- changing the accepted FSWEPP/Rock:Clime to WEPPcloud/`wepppy` to cligen-rs
  pedigree;
- changing PRISM data, station selection, localization, generation, output
  climate bytes, the Cargo acquisition model, or the generation profile; and
- unrelated authors who happen to share a surname in literature-review
  material outside the PRISM comparator authority surface.

## Authority

- Operator correction preceding commit `4af0470` establishes the attribution
  boundary.
- Commit `188f8ec` is the superseded record; `4af0470` is its forward
  correction and precedes the first changed-mode output.
- SPEC-A10-STOCHASTIC-PRISM-COMPARATOR revision 3 and method-record SHA-256
  `2c6668828292cb95c167fea4249eff89762901deba03c702bff0d26036c18924`
  are the current public authority.
- The completed parent package disposition is
  `PRISM-MODE-BUNDLE-PEDIGREE-READY`.

## Plan

1. Freeze scope, commit identities, canonical pedigree, scan surfaces, and
   prohibited fingerprints before executing the audit.
2. Scan the current tracked authorities and confirm the forward correction
   relationship.
3. build and inspect the Cargo crate, a fresh comparator output, and both
   published release bundles.
4. Apply only bounded current-tree corrections if the audit finds a residual.
5. Run package verification and repository gates, then close the package and
   reconcile the roadmap and catalog.

## Gates

- exact embedded/work-package method-record identity and canonical three-stage
  pedigree;
- no prohibited fingerprint on any frozen current public surface;
- Cargo payload includes the method/distribution records, excludes PRISM map
  payloads, and passes `cargo package` verification;
- fresh `prism run` emits the exact method record and binds it in the artifact
  manifest;
- both release assets retain their registered identities and have clean
  attribution-bearing text surfaces;
- the correction relationship is present and no history rewrite is attempted;
- `cargo fmt --check`;
- `cargo clippy --all-targets -- -D warnings`;
- `cargo test`; and
- `git diff --check`.

No production function changes are planned, so llvm-cov and CRAP are not
triggered. If execution changes a production function under `crates/`, both
gates become mandatory.

## Exit criteria

`PRISM-RESIDUAL-ATTRIBUTION-CLEAR` requires every current/public scan and
packaging gate to pass with no behavioral change. A residual in a current
authority or distributable artifact must be corrected and reverified. A
residual confined to superseded git history is documented as non-authoritative
and does not justify destructive history rewriting.

## Artifacts

- `artifacts/design-freeze.md` — immutable audit and claim boundary;
- `artifacts/audit-contract.json` — machine scan scope and fingerprints;
- `artifacts/verify.py` — fail-closed current-surface verifier;
- `artifacts/cargo-package-files.txt` — exact Cargo payload inventory;
- `artifacts/audit-results.md` — executed surface-by-surface evidence; and
- `artifacts/execution-disposition.md` — terminal package decision.
