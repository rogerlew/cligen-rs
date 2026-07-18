# Prospective amendment 004 — inference-mode RSS measurement

## Trigger

Lineage R4 job `1013873` completed the first frozen configuration and passed
every scientific, generation, benchmark-completeness, dispersion, runtime,
checkpoint, and parameter gate. Its isolated CPU-export subprocess reported
3,339,460,608 peak RSS, above the frozen 2 GiB safeguard.

Inspection found that the fresh subprocess loaded the export in evaluation
mode but invoked it with PyTorch gradient recording enabled. That is not the
frozen inference workload: evaluation mode controls layer behavior, while
`torch.inference_mode()` controls autograd recording and inference-only tensor
handling. The measured allocation therefore included an avoidable 100-year
autograd graph.

## Prospective correction

Starting with the next source commit and a new toolkit lineage, the isolated
RSS subprocess invokes the exact same 100-year export under
`torch.inference_mode()`. No model, data, seed, training, scoring, generation,
benchmark, threshold, grid, or promotion rule changes. R4 remains a failed
attempt and is not promotion evidence.

## Disposition

This is measurement conformance, not threshold relaxation. The frozen 2 GiB
RSS safeguard remains unchanged. Lineage R4 stops after the diagnostic first
configuration so that the remaining eleven allocations do not repeat a known
non-inference measurement defect.
