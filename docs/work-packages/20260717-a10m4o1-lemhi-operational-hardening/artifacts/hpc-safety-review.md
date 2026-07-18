# Independent HPC safety review — round 1

Reviewer: `toolkit_hpc_safety_review`
Verdict on initial scaffold: `ACCEPT-WITH-CHANGES`

The exact-marker recovery direction was appropriate, but safe execution
required stronger reservation, liveness, ledger, evidence, and admission
contracts.

| ID | Severity | Finding | Required disposition |
|---|---:|---|---|
| HS-01 | P1 | A recovery role is not useful if primary work consumes the remaining ceiling. | Reserve a frozen recovery contingency with the primary; retain it through ambiguity; release only after verified cleanup. |
| HS-02 | P1 | Node name plus marker was insufficient to prove deletion safe after requeue or unsettled scheduler steps. | Derive the node from authenticated terminal accounting; prove all jobs/steps/requeues absent and settled; bind marker to full authority/run/attempt/job/node/base/target/UID; validate twice; otherwise remain incomplete. |
| HS-03 | P1 | An arbitrary ledger state root could reset or roll back resource accounting. | Bind live authority to one private absolute ledger anchor, genesis, and hash chain; reject missing, copied, truncated, alternate, stale, or rolled-back state. |
| HS-04 | P1 | Projection failure occurred before a durable state that could authorize exact cleanup. | Record private `RAW_COLLECTED` and gates first; preserve cleanup marker data; authenticate the transformation; prevent projection from changing gates. |
| HS-05 | P2 | Wrapper signal and terminal precedence remained underspecified. | Supervise a process group; forward/wait; write status atomically; always attempt local cleanup; let cleanup/status uncertainty dominate application exit. |
| HS-06 | P2 | Free-space checking could race or omit expanded products/checkpoints. | Restrict provider bases; verify filesystem/owner/perms; size expanded manifest and products with margin/floor; serialize claims; recheck major expansion; never delete unrelated state. |
| HS-07 | P2 | Reuse paths could collide, overwrite, or invalidate later revisions. | Use content-addressed immutable paths, stable markers, and append-only run-revision manifests; test parallel and same-name/different-hash cases. |
| HS-08 | P2 | Ambient login/submission variables could silently change the compute environment. | Use `--export=NONE` or proved equivalent; reconstruct an allowlist and exact paths; reject overrides; set CUBLAS determinism before Python import; test hostile environments. |
| HS-09 | P2 | Layout validation only on compute would make failures expensive and could miss controller archive mistakes. | Validate archive/layout/vendor relations during local prepare and exact versions, loader, compiler, and build smoke on compute. |
| HS-10 | P3 | Transfer records needed deterministic units and safe partial-transfer semantics. | Use integer nanoseconds; permit resume only with provider range-integrity proof; verify/replace/remove SCP partials; recheck SSH masters. |

No finding authorizes direct compute-node SSH, broad deletion, live allocation,
or remote mutation.
