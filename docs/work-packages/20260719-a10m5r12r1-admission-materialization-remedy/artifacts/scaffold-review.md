# Scaffold review

Date: 2026-07-20
Disposition: `ACCEPT`

Review scope:

- bind the terminal A10M5R12 admission-materialization failure and cleanup;
- prove normalized byte identity of all inherited science/runtime sources;
- require fresh package/run/budget/authority identities;
- snapshot the exact current private toolkit state and authenticated job
  receipts before each submission;
- authenticate the staged checker and its PASS receipt against source, role,
  run, package, state hash, and all admission gates;
- prevent stale receipt reuse and fail on state mutation during snapshot;
- preserve serialized same-wave bootstrap by requiring the first candidate's
  ready-for-science setup before admitting the second; and
- leave confirmation and solar sealed.

The CUDA/Torch continuous-core self-test remains a fail-closed pre-training
gate on the admitted L40. The inherited P2 leap flag and calendar-bin estimand
limitations remain unchanged, and rolling-origin sensitivity remains required
before promotion.

Independent review initially rejected execution because the controller did
not atomically bind admission to submit, remote receipt handling was not
idempotent, the role sequence lacked executable coverage, operational
predecessor evidence was under-bound, and the staged checker did not bind its
own source and manifest. The accepted revision:

- makes toolkit `submit` authenticate the role receipt against the exact
  current private state while holding the run lock and before reservation;
- snapshots state and authenticated job receipts, verifies the published
  materializer, invokes the staged checker only when its immutable remote
  receipt is absent, and atomically promotes an authenticated local receipt;
- binds the staged manifest, checker source, predecessor terminal records, and
  exact control/first/second admission order;
- proves control, first candidate, second candidate after ready setup, stale
  setup rejection, stale toolkit state rejection, and immutable receipt reuse;
  and
- creates the plan-fixed controller receipt directory before strict toolkit
  plan validation.

The reviewer found no remaining blocker to publication or GPU execution.
