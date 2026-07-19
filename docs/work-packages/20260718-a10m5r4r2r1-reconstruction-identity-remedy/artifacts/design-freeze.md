# A10M5R4R2R1 prospective corrective freeze

R2 accessed only its first model's reconstructed output. That role reproduced
the accepted checkpoint payload and semantic state exactly but failed the
separately frozen outer TorchScript archive hash. A TorchScript file is a ZIP
container whose serialization metadata is not the learned model state, so its
whole-file digest is retired as a reconstruction gate. The mismatch remains
part of R2's immutable evidence.

R2R1 requires four independent exact identity classes before generation:

1. checkpoint payload byte length and SHA-256;
2. checkpoint epoch, global step, training seed, and corpus cursor;
3. canonical model-record file SHA-256; and
4. capacity, parameter count, hidden size, family, and the three accepted
   validation scores recorded by the export metadata.

The reconstructed TorchScript archive byte length and digest are retained in
each stream receipt for provenance. Loading must succeed, and the already-
frozen physical-support and stream-count gates remain mandatory. No accepted
archive digest is compared.

The R2 temporal contract and sites are incorporated by hash and are not
restated or changed. The original wrapper's nested Python newline is corrected
prospectively, and both `streams.json` and `evidence.json` exist on every
settled path. This package has not accessed any R2R1 generated output.
