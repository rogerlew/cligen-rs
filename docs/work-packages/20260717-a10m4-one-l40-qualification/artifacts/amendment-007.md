# Amendment 007 — propagate observed-window cursor

Status: prospective before run 8

Run 7 (`9d21665`, Slurm `1013773`) passed the finite first GPU update and
published the atomic checkpoint. Its fresh restart process then settled
`FAILED (1)` after 201 seconds because `run_restart` retained the original
literal batch offset `1`; the new training process had selected observed-window
offset `366`. The sanitized evidence archive was collected normally at 20,480
bytes with SHA-256
`30e22b41b5b2f01176859077bbf8631c058193f65ff66919142657c55cea6e6c`,
and exact remote cleanup/close passed.

Record `window_offset` in the already-required `corpus_cursor` checkpoint
state. The fresh process must load that checkpoint before constructing batch 2
and use `window_offset + 1`, exactly matching the uninterrupted control. This
is checkpoint state propagation, not a change to data selection or restart
tolerance.

No model, optimizer, role, normalization, corpus, dependency, allocation,
gate, or selector contract changes. Run 8 receives a new 120-GPU-minute intent,
bringing cumulative requested use to 845 GPU-minutes including the five-minute
recovery allocation, below the 2,400-minute ceiling.
