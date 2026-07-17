# A10M2 correction handoff

A10M2 remains immutable at `EXECUTED-HOLD-CUDA-ENVIRONMENT`. A10M2D1 supplies
the missing corrective evidence without rewriting that terminal.

For a separately authorized continuation of Lemhi GPU integration:

1. select CUDA directly at `/usr/local/cuda-12.8` rather than relying on the
   unresolved compute-node module;
2. compile with explicit `/usr/bin/g++` as the simplest observed working host
   compiler, or explicitly use advertised GCC 11.2;
3. record the compiler and runtime paths in provenance;
4. retain the one-L40 typed GRES and `gpu-icrews` priority path already proved;
5. restart at the unchanged CUDA smoke before proceeding to framework,
   distributed, or restartability gates; and
6. do not treat either working path as administrator-supported until confirmed.

A10M2D1 does not authorize A10M3 or any PyTorch/NCCL/restart submission.
