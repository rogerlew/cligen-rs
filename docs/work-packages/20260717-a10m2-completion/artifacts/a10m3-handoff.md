# A10M3 handoff

Prerequisites:

- `A10M1-CORPUS-READY` — satisfied;
- `A10M2-COMPUTE-READY` — satisfied by this package;
- scored development output — none produced;
- confirmation target access — false.

A separately scaffolded A10M3 may now freeze the model, training, generation,
selector, benchmark, schema, and finite resource contracts in the study plan.
This terminal does not execute A10M3 or authorize confirmation access.

Operational constraints to carry forward:

- `rmm` requires University of Idaho VPN plus human password/Duo bootstrap;
  agents use only warm `BatchMode=yes` masters and have in-package authoring
  and execution authority under the compute guide;
- use `gpu-icrews` and typed `gpu:l40` requests;
- use `/usr/local/cuda-12.8/bin/nvcc -ccbin=/usr/bin/g++` for the proved
  standalone compiler path;
- the proved framework environment is Python 3.8.11 with
  `torch==2.4.1+cu124`; treat it as M2 evidence, not an automatic M3 product
  selection;
- if retained, create the venv at its final path, isolate Python/loader paths,
  invoke entrypoints through `python -m`, and explicitly add/test NumPy before
  any NumPy conversion;
- stage only A10M1's accepted v2 98-object manifest, use archive/`.part`/hash
  transfer rules, verify before use, and preserve durable fallback;
- use A10M2D2's control-host rates for transfer planning; do not use stage-2's
  warm-cache rates as cold or training throughput;
- instrument real loader, checkpoint synchronization, CPU/GPU memory, and
  generation-runtime behavior in M4 because M2 made no performance claim; and
- retain the confirmation firewall and all A10M1 role/normalization
  restrictions.

The next package is `A10M3 — Model, training, generation, and selector freeze`.
