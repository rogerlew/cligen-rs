# Amendment 04 — venv entrypoint and resource rebalance

Date: 2026-07-17 PDT
Applied after C2-01 and before C2-02

## Evidence

C2-01 (`1013672`) received two distinct L40s but failed after one second with
exit `126:0` before importing PyTorch. C1 created the venv at a temporary
durable name and atomically renamed it after installation. The venv interpreter
still works, but `bin/torchrun` retained an absolute shebang to the former
temporary path. No NCCL or DDP gate ran.

## Prospective correction

- Require `runtime/pytorch/bin/python` and invoke
  `python -m torch.distributed.run` instead of the stale console script.
- Reduce C2-02 from five to two minutes; C1 proved framework startup and C2-01
  reached its prelaunch checks in one second.
- Reduce still-unrun C3a/C3b from five to two minutes. For C3a, change the
  signal offset from 240 seconds before a five-minute limit to 90 seconds
  before a two-minute limit, retaining delivery about 30 seconds after start.
  The state recurrence, checkpoint rule, interruption code, resume target, and
  pass criteria do not change.

Conservative requested use becomes:

| Attempts | GPU-minutes |
|---|---:|
| C1-01 + P0 + C1-02 | 35 |
| C2-01 | 10 |
| C2-02 | 4 |
| C3a + C3b | 4 |
| **Final planned total** | **53** |

This remains below the hard 60-GPU-minute ceiling. The stale-shebang trap is a
handoff requirement: future packages create a venv at its final durable path
or invoke entrypoints through the interpreter module.
