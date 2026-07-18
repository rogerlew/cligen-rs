# A10M5R1 prospective diagnostic freeze

The first hypothesis is that the roughly 3.1 GiB floor is dominated by the
canonical PyTorch CPU backend or loader rather than model parameters: A10M5
exports ranged from 152,332 to 927,000 bytes while RSS remained within
3,317,673,984--3,363,221,504 bytes.

The diagnostic ordering is fixed from least to most invasive:

1. phase-resolved memory attribution on the current streaming TorchScript
   export;
2. output-preserving eager/TorchScript and backend toggles already in the
   canonical closure;
3. allocator and loader isolation with exact output comparison;
4. an already-supported minimal loader outside Python, if present;
5. stop and request a material decision before quantization, approximation,
   dependency expansion, model change, or threshold change.

Every variant uses synthetic features or candidate-fit-only state, a 100-year
365-day chunk schedule with exact hidden-state carry, GPU hidden during CPU
measurement, one pinned core, and one thread in PyTorch, OpenMP, MKL, and
OpenBLAS. The 2 GiB, 250 MiB export, 15-second cold-load, 10/30-second absolute
warm, and 5x/10x ratio thresholds are unchanged.
