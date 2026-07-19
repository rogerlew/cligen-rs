# A10M5O2D1 execution disposition

Terminal: `A10M5O2D1-L40-INTERCONNECT-CHARACTERIZED`

The live diagnostic completed within authority and answered the frozen
question. Node03 provides peer-capable PCIe paths among every L40 pair, with
approximately 20.1 GB/s on pairs 0–1 and 2–3 and 14.5–14.6 GB/s on the other
pairs for 128 MiB two-rank all-reduces. NCCL 2.26.2 uses those P2P paths for
two ranks but selects shared-memory host staging for the full four-rank group,
collapsing bus bandwidth to approximately 1.15 GB/s. External InfiniBand is
initialized but is not the measured collective channel.

This terminal characterizes the current canonical behavior; it does not
promote a four-GPU tuning workaround. The canonical default stays one L40,
two-L40 use remains workload-qualified, and four-L40 performance use is held
pending proof of a supported remedy.
