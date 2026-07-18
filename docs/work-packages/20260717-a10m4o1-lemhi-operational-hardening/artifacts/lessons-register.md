# A10M4 operational lessons register

This register separates generic orchestration defects from application-owned
contracts. A remedy is not allowed to broaden because it happened to be useful
for one A10M4 script.

| ID | Evidence / stumble | Root cause | Owner | Prospective remedy |
|---|---|---|---|---|
| L01 | r1: Cargo present, `rustc` absent | Asset selection validated a component, not the coupled build closure | Toolkit/provider | Add a compute-safe toolchain provider with required executable/archive members, versions, target, compiler paths, licenses, and registered build smoke. |
| L02 | r3: Cargo vendor directory resolved one level too high | Archive identities passed, extracted layout semantics did not | Toolkit + package | Add declared layout assertions and an offline exact-layout preflight before submission; package retains its build command. |
| L03 | r4: deterministic CuBLAS environment absent | Required determinism environment was implicit in the application | Toolkit/configuration | Freeze required job environment in the plan/provider, render it in the wrapper, record it without unrestricted dumps, and fail before scientific entry. |
| L04 | r4/r6: raw traceback contained the private Ceph root and blocked collection | Collection conflated authenticated raw retrieval with publishable projection | Toolkit | Emit private `RAW_COLLECTED` first so cleanup remains authorized; apply typed boundary-aware projection, transformation authentication, and the unknown-leak scan separately. |
| L05 | r5: earlier failures left job-local trees and exhausted node03 `/tmp` | Cleanup depended on reaching the normal receipt path; scheduler purge was assumed but not proved | Toolkit/storage | Version storage as `toolkit_recoverable`; a toolkit supervisor owns marked state, performs serialized capacity admission, forwards signals, cleans catchable exits, and requires exact-node recovery otherwise. |
| L06 | recovery needed a separate five-minute allocation | Direct compute-node cleanup is prohibited and no recovery role/capacity was reserved | Toolkit/scheduler | Reserve bounded recovery capacity before primary submit; after authenticated terminal settlement, run one exact-node/exact-marker recovery job and verify absence without broader placement. |
| L07 | r2 used a different authority identity and failed before submit | New-run continuation required error-prone private JSON editing; arbitrary state roots can reset the current ledger | Toolkit/UX | Add immutable authority revisions and safe run derivation against one canonical hash-chained ledger anchor; give new dispatches one exclusive genesis, publish head checkpoints, reconcile scheduler accounting before live spending, and never initialize an alternate ledger. |
| L08 | Every corrected run retransferred a 4.83 GB closure | Corrections required new runs/source commits; current stage-once matrix behavior was not the problem | Deferred operations | Record integer transfer telemetry and encourage one multi-job matrix. Defer cross-run caching/reuse until ownership, quota, licensing, reference, and garbage-collection semantics are separately designed. |
| L09 | r6 selected an intentional masked Daymet row | Corpus missingness semantics were not carried into window selection | Application/docs | Add a guide/package checklist: select fully observed windows under the corpus contract, do not impute, and record the chosen window. No generic toolkit data inference. |
| L10 | r7 omitted selected-window offset from restart | Checkpoint cursor was incomplete for the actual sampler | Application/docs | Require application checkpoint manifests to name every cursor needed for the next batch and prove fresh-process equivalence. Toolkit authenticates the receipt but does not invent state. |
| L11 | r8 restored CPU RNG bytes directly onto CUDA | Deserialization placement was conflated with destination model placement | Application/docs | Document CPU-first checkpoint deserialization and explicit relocation of model/optimizer state; retain independent CPU/CUDA RNG restoration tests. |
| L12 | r9/r10 used brittle faithful line-count hypotheses | Completeness was inferred from guessed format structure | Application/docs | Require format-aware parsing or a byte-pinned fixture, including headers/footers/calendar, before declaring output complete. Toolkit sees only the registered boolean gate. |
| L13 | Stage receipts omitted the transfer timing required by the spec | Foundation implementation lagged the normative transfer receipt | Toolkit | Record integer `elapsed_ns`, bytes, provider-supported transfer state, and integer observed-rate floor; reverify live remote identity before any skip. |
| L14 | A10M4 actual storage/determinism semantics exceed canonical `v1` | The canonical record claims scheduler-purged job-local storage and omits required deterministic CUDA environment; its hashed status/evidence cannot be mutated safely | Canonical successor | Preserve `v1` as status-at-issuance history; split immutable successor semantics, immutable smoke attestation, and a versioned canonical designation that advances only after smoke. |
| L15 | Most two-step diagnostic CPU ratios exceeded 10x | Binary baseline is exceptionally optimized and qualification weights are not a candidate | Deferred science | Preserve raw timings. Revisit 5x/10x only in a separate prospective selector-contract package; do not change it here. |

## Priority before A10M5

L03--L07, L13, and L14 are operational prerequisites for new commitments.
L01--L02 are required whenever a package builds Rust or another native tool
closure. L09--L12 become mandatory authoring checks for A10M5 but remain
application-owned. L08 and L15 are explicitly deferred and receive no false
claim of resolution from this package.
