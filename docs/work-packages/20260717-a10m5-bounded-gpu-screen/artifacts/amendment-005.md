# Prospective amendment 005 — bounded-memory recurrent export

## Trigger

Lineage R5 job `1013874` repeated the first frozen configuration with the
isolated subprocess correctly under `torch.inference_mode()`. Peak RSS remained
3,314,724,864 bytes. The job also independently failed one faithful timing row
at MAD/median `0.1013728583` after its one rerun and two permitted paired
discards; that bounded dispersion failure remains final for R5.

The RSS result isolates a second conformance defect. Both the Python candidate
and its traced export passed all 36,525 days to the GRU at once. PyTorch then
allocated a full-sequence recurrent workspace. The accepted A10M4 candidate
instead used bounded 365-day chunks and carried the recurrent state between
chunks. The M5 implementation was therefore measuring an avoidable batch
realization rather than the intended bounded-memory CPU generation surface.

## Prospective correction

Starting with the next source commit and a new toolkit lineage:

- the inference export accepts and returns the single-layer GRU hidden state;
- 1/30/100-year generation is evaluated in chunks of at most 365 days;
- the exact returned hidden state is supplied to the next chunk;
- the isolated RSS subprocess invokes that same export protocol; and
- the existing prefix, order, identity, support, cold-load, timing, export-size,
  and 2 GiB RSS checks remain unchanged.

This does not truncate history, reset state, change weights, modify training,
alter the grid, relax a threshold, or read another data role. It is the
bounded-memory realization of the same recurrent computation.

## Disposition

R5 remains a failed diagnostic attempt and cannot promote. Its exact remote
root is removed after the toolkit observes the terminal receipt. The successor
restarts from the first configuration so every promotable row uses one export
and generation protocol.
