# Framework environment selection

Status: NOT REACHED

The frozen design requires J1's successful compiler/driver/kernel receipt
before choosing a Python/PyTorch/CUDA stack. J1 failed at host compilation, so
no framework version was selected, no wheelhouse was downloaded, no license
bundle was created, and no compute-node environment was reconstructed.

This is a deliberate fail-closed outcome, not missing evidence. Framework
selection must occur only in a newly authorized attempt after the CUDA host
compiler path passes.
