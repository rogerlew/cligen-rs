# A5f1 Internal Review

## Verdict

**ACCEPT** — A5f1 removes the unshipped A5e0 runtime surface while preserving
the accepted scientific record and the faithful generator.

## Review scope

This review checked the release-exposure decision, removal completeness,
source restoration, preservation of accepted A5e0/A5f0 records, repository
validation gates, and the resulting roadmap state.

## Findings

### Release-exposure decision

The removal decision is supported by the evidence in
`release-exposure-audit.md`:

- no exact `cligen` crate exists in the crates.io API or sparse index;
- the workspace package resolves locally as unpublished version `0.1.0`;
- the repository releases and tags predate the A5e0 implementation commit;
- the A5e0 implementation remains recoverable from Git history.

The runtime was therefore **unshipped**. Direct removal is preferable to a
deprecation shim because there is no released compatibility contract to
preserve and a shim would retain the accidental complexity A5f1 is intended
to retire.

### Removal completeness

The A5e0 library module and example runner are absent. The package verifier
also confirms that no production source reference, Cargo target, or packaged
file exposes the retired runtime.

The affected production paths match their pre-A5e0 forms at commit
`27e5e7754bdfafcca649a71d0f5576910433d0d3`. This establishes that A5f1 is a
retirement and restoration change rather than another redesign of the
generator or random-number machinery.

### Scientific-record preservation

The accepted A5e0 specification, schemas, report, manifest, and A5e0/A5f0
package records remain byte-identical to the A5f1 baseline manifest. Their
registry status now states that the runtime is retired while the historical
record remains available.

Historical A5e0 producers and verifiers must be run from the recorded A5e0
implementation commit, not from current `main`. This is intentional: current
`main` preserves the evidence but no longer presents the rejected runtime as
a supported feature.

### Fidelity and scope

No vendored Fortran file changed. The faithful generator remains covered by
the full test suite and CLI-parity gate. A5f1 makes no new scientific claim,
changes no climate-model structure, and adds no successor mechanism.

### Roadmap consistency

A5f1 is removed from the active queue and recorded as complete. A7a is now the
first active corrective action. A5f1 does not pre-authorize or scaffold A7a;
that work remains a separately dispatched package.

## Open findings

None.
