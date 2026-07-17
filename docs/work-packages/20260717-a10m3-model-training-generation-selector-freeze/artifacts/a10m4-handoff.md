# A10M4 handoff

A10M4 is authorized only after this package reaches
`A10M3-DESIGN-FROZEN`. Its purpose is implementation qualification, not model
selection or scored development.

It must use canonical configuration `lemhi-a10-py311-l40-v1` at semantic
SHA-256
`0b1115a6801259c62d9550c877a3c49a897319348ba1c2027be0d9c4f77c1179`,
the accepted 98-object A10M1 v2 transfer manifest, and `gpu-icrews` typed
`gpu:l40:1`. Python 3.8 cannot be an automatic fallback.

The smallest sufficient qualification is:

1. stage and hash the accepted corpus; demonstrate role-filtered sampling and
   normalization using only `candidate_fit`, with validation excluded from
   gradients;
2. instantiate the smallest stable-ID N0 configuration (latent 32, width 128,
   depth 2, lognormal tail), record its exact parameter count, and perform one
   finite forward/backward/optimizer step on real fit data;
3. atomically checkpoint every required state, reload it in a fresh process,
   and show the next batch/update is exact under the recorded tolerance;
4. generate deterministic 1-year smoke plus nested 30/100-year structural
   fixtures using Philox counters, checking support, dates, order independence,
   and identical 30-year prefixes;
5. produce a portable one-core CPU export and execute the representative
   six-station benchmark protocol as a qualification diagnostic, not a
   candidate runtime verdict;
6. record wall time, GPU peak memory, CPU peak RSS, stage bytes/rates, export
   bytes, checkpoint bytes/interval, and projected screen cost;
7. clean the exact remote root and preserve sanitized toolkit evidence.

The M4 budget is at most 40 requested L40 GPU-hours, with jobs bounded by the
single-job envelope in `model-training-generation-v1.json`. Start with one
two-hour job; retries require a pre-output implementation amendment and remain
inside the 40-hour ledger. A scientific score, development-series read,
confirmation target access, grid/threshold change, or model-family rescue is
out of scope.

Success terminal: `A10M4-QUALIFICATION-READY`. Holds name the exact failed
loader, training, restart, generation, export, resource, or environment gate
and preserve evidence. An implementation-only correction may remain inside
A10M4 before any scored output; a scientific-contract change requires a new
development package and cannot inherit the A10M3 freeze identity.
