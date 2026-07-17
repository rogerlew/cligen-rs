# Documentation drift classification

Checked 2026-07-16 against live login, Slurm, and D1 evidence.

| Published claim | Classification | Evidence |
|---|---|---|
| The GPU workshop lists two L40s on both `node03` and `node04`. | Drifted and contradicted | Current partition documentation and live Slurm expose four L40s on `node03` and four RTX A6000s on `node04`. |
| The GPU workshop loads `cuda/12.2` from `/opt/modules/modulefiles` inside a GPU job. | Drifted and contradicted | Live CUDA is 12.8. On `node03`, the directory exists but cache-bypassed discovery/load of `cuda/12.8` fails. |
| CUDA can be compiled before submission and the binary run on a GPU node. | Current only with qualification | C1/C2 login-built binaries pass. Ambient C0 retains the AVX-512 Spack runtime and dies on `node03`; the compiler/runtime must be explicit and node-compatible. |
| The Lemhi login server has the same processor generation as Lemhi nodes. | Contradicted for `node03` | Login is Intel Xeon Gold 6148 with AVX-512; `node03` is AMD EPYC 7313 without the tested AVX-512 features. |
| The current Getting Started Core GCC 12.1 hierarchy represents the active compiler environment. | Drifted | The observed ambient compiler is GCC 12.5 from a newer architecture-specific Spack production tree. |
| The Ollama recipe's alternative module directory exists on GPU nodes. | Partly current | The directory exists on `node03`; CUDA resolution from it fails. The recipe's Python module was outside the frozen matrix and remains untested. |

Sources:

- <https://docs.c3plus3.org/docs/workshops/Cluster/GPU_Nodes.html>
- <https://docs.c3plus3.org/docs/help/Tutorials/Partitions.html>
- <https://docs.c3plus3.org/docs/workshops/Linux/>
- <https://docs.c3plus3.org/docs/help/Getting_Started/>
- <https://docs.c3plus3.org/docs/help/Tutorials/Ollama.html>
