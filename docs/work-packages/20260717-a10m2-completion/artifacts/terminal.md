# Terminal

Disposition: `A10M2-COMPUTE-READY`

The completion package closes the A10M2 capability milestone while preserving
the original A10M2 hold and D1/D2 evidence. On the I-CREWS-priority
`gpu-icrews` path it proved:

- corrected CUDA 12.8 compilation and execution on one L40;
- complete hashed offline reconstruction of compute-valid PyTorch
  2.4.1/CUDA 12.4 under Python 3.8.11;
- one-L40 autograd, optimizer, checkpoint, and reload behavior;
- verified A10M1 Ceph/XFS stage 2 with all 98 objects, bundled form, bounded
  reread, durable-class copy-back, fallback, and exact local cleanup;
- two distinct L40s, NCCL 2.20.5 all-reduce, one DDP update, identical final
  parameters, and clean process-group shutdown; and
- actual Slurm `USR1`, atomic durable checkpoint, expected interruption, and
  exact manual resume/control equivalence.

The package used 53 requested and 2.0167 actual GPU-minutes, retained no remote
run, left an empty queue, accessed no confirmation target, and changed no
production generator behavior. A10M1 is already `A10M1-CORPUS-READY`; the two
entry conditions now authorize separately scaffolded and dispatched A10M3.
