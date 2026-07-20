# Scaffold review

Date: 2026-07-19
Disposition: `ACCEPT FOR PUBLISH/EXECUTION`
Reviewer: independent `hpc_execution_audit` agent, with delegated OU math review

No P0, P1, or P2 findings remain open.

The initial review rejected execution until the scaffold excluded the binary
leap-year feature from new loadings, authenticated selector inputs, retained
raw streams and checkpoints, removed conditional-member NLL from optimization,
expanded dynamic tests, separated the full corpus preflight from the compact
control expectation, and bound source/runtime/comparator identities. Each
finding was implemented and re-reviewed.

The final review independently accepted:

- the exact OU recurrence, stationary scaling, FFT linear convolution, learned
  time-scale bounds, matched medium initialization, and common random fields;
- month/year labels as aggregation-only for new state and loading dynamics;
- the complete seed/site/member matrix and retained raw/checkpoint evidence;
- exact published-source, collection, admission, runtime, comparator-binary,
  per-site localization, corpus, and calendar identities;
- inherited temporal eligibility plus non-gating order-preserving annual
  diagnostics; and
- the resource/admission/cleanup sequence for concurrent L40 execution.

The toolkit binary-evidence revision was separately re-reviewed and accepted.
Sanitizer version `lemhi-evidence-projection-5` keeps allowlisted `.npz` and
`.pt` evidence byte-exact, scans forbidden byte strings, and binds raw and
projected hashes. Unit coverage includes both the projection function and an
end-to-end collection path.

The accepted limitations remain explicit: frozen P2 still consumes its
inherited leap-year flag; fixed calendar-bin evaluation does not prove scale
invariance; and a qualifying candidate requires random-origin rolling-window
sensitivity before promotion. The Torch/CUDA continuous-core self-test runs on
the admitted L40 before any training because Torch is absent from the local
controller environment.
