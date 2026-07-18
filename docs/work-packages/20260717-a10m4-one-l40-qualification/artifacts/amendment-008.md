# Amendment 008 — restore RNG state on CPU

Status: prospective before run 9

Run 8 (`f7984cb`, Slurm `1013774`) passed the finite observed-window update,
loaded the propagated cursor, and entered fresh checkpoint restoration. It
settled `FAILED (1)` after 196 seconds because `map_location=cuda` moved the
saved CPU RNG ByteTensor to the GPU before `torch.set_rng_state` consumed it.
The sanitized evidence archive was collected normally at 20,480 bytes with
SHA-256
`fc5370abafc589e6ea6c5a2fe148bbab9d2228c7ab1ade9fdf2875b827c11ed4`,
and exact remote cleanup/close passed.

Deserialize the checkpoint on CPU. `load_state_dict` then copies model state
into the already-created GPU module and PyTorch relocates optimizer state to
its GPU parameters, while CPU and CUDA RNG restoration each receive the
native CPU ByteTensor representation saved by `torch.save`. Cursor selection,
state contents, and exact restart comparison are unchanged.

No scientific, model, optimizer, corpus, dependency, allocation, gate, or
selector contract changes. Run 9 receives a new 120-GPU-minute intent,
bringing cumulative requested use to 965 GPU-minutes including the recovery
allocation, below the 2,400-minute ceiling.
