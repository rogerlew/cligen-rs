# A11E5D — Directional Error Attribution

Status: `SCAFFOLDED`

Date: 2026-08-27

Evidence mode: observed development replay; confirmation sealed

Starting branch and push target: current `origin/main`, push `main`

## Objective

Determine whether A11E5's dispersion errors are systematically over- or
under-dispersed, distinguish bias from scatter, and quantify whether circular
block produces more or less variance than Gaussian.

## Authority

- [SPEC-A11-DIRECTIONAL-ERROR-ATTRIBUTION](../../specifications/SPEC-A11-DIRECTIONAL-ERROR-ATTRIBUTION.md)
- closed A11E5 evidence and exact execution source
- operator authorization to run the directional diagnostic before hybrid design

## Scope

Included: exact A11E5 replay, signed monthly and annual variance ratios, signed
annual persistence and low-frequency residuals, bias/scatter decomposition,
treatment/control dispersion comparison, deterministic replay, review, gates,
and reconciliation.

Excluded: changing either generator, fitting or selecting a hybrid, routing,
new data, confirmation, production, CLI changes, and WEPP claims.

## Plan and gates

1. Freeze specification, manifest, source, schema, and synthetic arithmetic.
2. Publish the exact diagnostic source on `origin/main`.
3. Replay 320 streams and require exact A11E5 metrics and stream hashes.
4. Replay outputs byte-identically, review the directional attribution, run
   repository gates, and reconcile records.

Required gates are strict manifest/schema tests, published source and closed
A11E5 identity, canonical calendar preflight, exact 160-pair replay, finite
directional evidence, zero daily invariants, confirmation=false,
byte-identical scientific outputs, review without P0/P1, standard Cargo gates,
`git diff --check`, and changed-document link validation. No production Rust
function changes occur, so coverage/CRAP is not triggered.

## Resource bound

One execution and one replay, each limited to the exact 320 local CPU streams.
No external service or scarce accelerator is used.

## Exit

Close with descriptive directional findings or an exact integrity HOLD. The
package cannot alter A11E5's scientific disposition.
