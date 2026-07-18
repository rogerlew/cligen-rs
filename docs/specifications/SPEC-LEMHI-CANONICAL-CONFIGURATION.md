# Lemhi canonical agent configuration

Status: authoritative (revision 2)

## Surface

This specification governs the versioned configuration record that selects
the default Lemhi GPU execution stack for A10 agent work. The current record
is
[`lemhi-a10-py311-l40-v1`](../../research/a10/lemhi_toolkit/configurations/lemhi-a10-py311-l40-v1.json).
It is a repository-controlled operational contract, not an administrator
claim about the cluster-wide default.

## Authority and scope

The accepted authority is the completed
[CPython 3.11 Lemhi smoke package](../work-packages/20260717-a10-lemhi-python311-smoke/package.md),
terminal `A10-LEMHI-PY311-SMOKE-READY`. Its final run authenticated 19 exact
runtime, standard-library, native-linkage, NumPy, PyTorch, CUDA, one-L40,
offline-install, and cleanup gates.

The configuration is canonical for A10 single-L40 Python work on Lemhi. It
does not establish performance, training readiness, multi-GPU behavior,
preemption/requeue behavior, production durability, administrator support, or
an A10M3 scientific result.

## Record identity

The record is UTF-8 JSON with no duplicate keys and schema version
`lemhi-canonical-configuration-1`. `configuration_semantic_sha256` is the
lowercase SHA-256 of the toolkit's canonical JSON serialization after removing
that field. Consumers MUST verify both `configuration_id` and this semantic
hash before staging or submission.

The record pins:

- the toolkit profile and ordered provider-definition hashes;
- target platform, accelerator, scheduler, storage, and isolation contracts;
- portable interpreter version, ABI, final path, bytes, hash, and license
  provenance;
- requirements lock, wheel manifest, wheelhouse, NumPy, PyTorch, and CUDA
  identities;
- the accepted gate receipt and work-package terminal; and
- explicit invalidation triggers, excluded claims, and legacy-fallback policy.

## Consumer policy

Every A10M3 or later work package that uses Lemhi GPU Python MUST prospectively
record:

1. `canonical_configuration_id`;
2. `configuration_semantic_sha256`;
3. whether it uses the configuration unchanged; and
4. any additional package-owned assets or gates that do not alter the
   canonical stack.

An unchanged consumer MUST use the pinned provider order, artifact hashes,
typed L40 request, offline install, final-prefix, isolation, evidence, and
cleanup contracts. It MAY choose a smaller time limit or greater package
memory/CPU request when scientifically justified, but it MUST NOT represent
those resource changes as a new runtime capability claim.

Silent dependency resolution, ambient modules, a moved virtual environment,
an untyped GPU request, compute-network installation, or automatic runtime
fallback is `CANONICAL_CONFIGURATION_DRIFT` and fails before submission.

## Legacy fallback

The A10M2 Python 3.8.11 / PyTorch 2.4.1+cu124 stack remains historical proved
evidence and an explicit legacy fallback only. It is not the current default.
Using it requires a prospectively named deviation, its original exact hashes,
and package-specific justification and gates. A missing or failed canonical
asset MUST NOT silently select it.

## Invalidation and replacement

Any trigger listed in the canonical record invalidates the current capability
for new commitments. The operator or agent MUST stop before submission,
create a new versioned candidate configuration, and execute the bounded Lemhi
smoke again. A passing replacement receives a new configuration ID; the old
record becomes `superseded` but remains immutable for historical consumers.

Changing only prose outside the record does not change its identity. Changing
any semantic record field requires a new immutable semantic record and smoke
package; evidence and designation are never inserted back into that record.

## Revision-2 immutable transition model

The v1 record is immutable historical status-at-issuance evidence. Its
embedded `current-canonical` value is not edited when a successor is assessed.
New configuration semantics use schema
`lemhi-canonical-configuration-semantics-2` and contain no mutable smoke or
promotion state. The lowercase semantic SHA-256 is computed after removing
only `configuration_semantic_sha256`.

A bounded live validation produces a separate immutable
`lemhi-canonical-smoke-attestation-1` record binding the exact configuration
ID and semantic hash. Passing evidence does not itself change the default.
Only a subsequent `lemhi-canonical-designation-index-1` revision may designate
the attested hash current and the prior hash superseded. A failed smoke is
retained as failed evidence, cannot mutate the candidate, cannot advance the
index, and cannot silently restore v1's invalidated storage semantics.

The candidate introduced by A10M4O1 remains noncurrent until its separately
dispatched smoke and designation revision pass. Consumers MUST resolve the
current configuration through the designation index once that index exists;
historical records remain directly addressable by exact ID and hash.
