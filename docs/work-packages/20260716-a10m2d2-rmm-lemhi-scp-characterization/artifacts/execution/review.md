# A10M2D2 review

## Findings

- P1: zero open findings.
- P2: zero open findings.
- P3: the frozen TAR estimate allowed at most 132 MiB round trip, while BSD
  tar padding produced 133.007 MiB. Actual-byte accounting kept the run 154.993
  MiB below the hard ceiling. Future packages must size the generated archive
  before freezing or launching its transfer.
- P3: `ssh -O check` reports on stderr, so the driver's stdout-only
  `control-masters.txt` capture was empty. The launch checks demonstrably
  passed before the script continued, and independent post-execution checks
  also passed. The receipt now records sanitized states. A future driver should
  capture both streams.

## Evidence audit

- All unexpected command statuses are zero; I256 status 124 is prospectively
  expected.
- All 27 integrity-ledger rows say `pass`.
- S1024 succeeded in both directions and therefore supports the frozen
  projection method.
- Small-file local, remote, and downloaded manifests compare exactly.
- The interrupted object was bounded between zero and its source size; rsync
  completed it and final SHA-256 passed.
- Logical bytes and peak remote retention stayed inside their hard bounds.
- Exact local and remote cleanup receipts say absent.
- Evidence contains no username, user home path, credential, Duo material,
  control socket, or private key material. The Ceph server list was sanitized.

## Scope audit

No Slurm/GPU resource, compute node, scientific data, LFS data, installation,
cold authentication, concurrency test, or Stage 2 action occurred. The result
is bound to one warm `rmm`/VPN/time window and is not an SLA.
