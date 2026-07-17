# Independent architecture and extensibility review

Reviewer: subagent `/root/toolkit_arch_review`
Mode: read-only; no file edits or remote operations
Draft reviewed: initial revision-1 specification scaffold of 2026-07-17

## Findings

| ID | Priority | Finding | Proposed correction |
|---|---|---|---|
| AR-01 | P1 | `sbatch` acceptance can precede durable job-ID recording, so retry is not idempotent. | Durable submission intent, resource reservation, unique Slurm token, reconciliation, and no blind retry. |
| AR-02 | P2 | The lifecycle lacks a common transition record and pre-plan transitions cannot bind a nonexistent plan. | Define a transition event; bind authority/config hashes before planning and semantic `plan_id` afterward. |
| AR-03 | P2 | “Canonical record” does not define deterministic JSON bytes. | Adopt RFC 8785/JCS and cross-serializer golden fixtures. |
| AR-04 | P2 | The minimum slice rendered mechanics but did not clearly implement every live command path. | Execute every path against injected fakes/temporary fixtures before the Python 3.11 live consumer. |
| AR-05 | P2 | Independently selected providers can compose into an ABI-incompatible stack. | Use an explicit ordered stack with machine-checkable `requires`/`provides`; no general solver in revision 1. |
| AR-06 | P2 | Generic executable provider hooks are both broad and underspecified. | Use declarative providers mapped to toolkit-owned typed operations and side-effect classes. |
| AR-07 | P2 | A POSIX-only remote runner contradicts the proven Bash Slurm contract. | Separate POSIX bootstrap/staging from profile-declared, probed job interpreters. |
| AR-08 | P3 | Hard-coded SSH aliases reduce profile portability and fixture quality. | Use logical endpoint fields with Lemhi aliases as revision-1 defaults. |
| AR-09 | P3 | Per-file license receipts are excessive for repository-owned assets. | Require exact license provenance for external redistributable assets; allow one repository reference for owned files. |
| AR-10 | P3 | Declaring rsync in the minimum slice without implementing it adds empty surface. | Implement SCP only in the minimum slice; retain rsync as a later static provider. |

## Reviewer conclusion

The direction was conservative and appropriate, but the initial draft had one
P1 and six P2 findings. The reviewer judged it implementation-ready only after
the submission, record/state, executable-slice, composition, provider, and
shell-boundary corrections were incorporated.
