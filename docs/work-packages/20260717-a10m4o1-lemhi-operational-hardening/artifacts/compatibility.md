# Revision-2 compatibility disposition

| Surface | Historical behavior | Hardened behavior | Compatibility rule |
|---|---|---|---|
| Records | `lemhi-toolkit-record-1` | `lemhi-toolkit-record-2` | Dual read; new v2 runs write v2 only; never rewrite v1. |
| Providers | API 1, six classes | API 2, seven classes including toolchain | A stack is all v1 or all v2; mixed execution fails before operations. |
| Storage | `scheduler_purged` accepted | `toolkit_recoverable` required | v1 remains historical; hardened plans reject purge assumptions. |
| Authority | Fixed source commit, caller state root | Immutable revisions, canonical anchor, exclusive genesis, reconciliation | v2 live CLI rejects arbitrary state roots and unpublished lineage. |
| Environment | Select variables cleared in scripts | `--export=NONE`, reconstructed allowlist, exact PATH/TMPDIR/CUBLAS | Ambient override fails before application import. |
| Evidence | Quarantine then leak scan | authenticated `RAW_COLLECTED`, typed projection, transformation receipt | Projection failure preserves cleanup authority and cannot change gates. |
| Transfer | bytes/hash/promotion | integer timing/rate/state and immediate skip revalidation | v1 receipts remain readable; v2 requires the new fields. |
| Canonical config | status and evidence embedded in v1 | immutable semantics, separate attestation, separate designation | v1 is status at issuance; candidate is noncurrent until index promotion. |

Raw SHA-256 of canonical v1 remains
`99a7df3d4192ccf9a585944f62501087126c855a4fe59964aa6106afe42ae312`.
No v1 provider, profile, receipt, or configuration file was modified.
