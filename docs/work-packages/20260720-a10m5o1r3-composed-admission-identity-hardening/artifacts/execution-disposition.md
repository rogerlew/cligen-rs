# Execution disposition

Terminal: `A10M5O1R3-COMPOSED-ADMISSION-IDENTITY-READY`

Disposition: `EXECUTED-COMPLETE`

The toolkit now models a composed admission controller as a versioned ordered
chain of logical plan assets. The semantic plan binds the chain. Under the run
lock and before reservation, `submit` requires the same ordered
`{logical_name, bytes, sha256}` projection in the current local files, private
prepared assets, promoted transfer receipts, and the self-authenticating
package admission receipt. The whole admission materialization contract is
immutable after verification.

Historical plans that omit the additive object retain their original
interpretation. The specification requires every newly authored composed
controller to declare it. The contract proves which checker identities were
authorized and claimed by the receipt; it does not claim generic control-flow
attestation, so package wrappers must continue authenticating delegates at
execution time.

All local, toolkit, shell, JSON, and repository gates passed. No allocation or
remote mutation occurred. The R14R2 abort remains immutable evidence of a
zero-attempt operational composition defect, and R14R2R1 may now be rebuilt
under fresh package, plan, authority, and run identities.
