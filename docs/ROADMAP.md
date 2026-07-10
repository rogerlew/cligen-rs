# cligen-rs Roadmap

Status: living — forward-only queue. Completed items move to the
[work-package record](work-packages/README.md).

Ordering principle: **fixtures before port, faithful before native,
port before augmentation.** Faithful-mode identity is the foundation every
extension stands on; an augmentation landed before its substrate is
port-parity-tested is unverifiable.

## Queue

| # | Item | Mechanism | Acceptance |
|---|---|---|---|
| 7 | **Observed mode** | `day_gen` (`.prn` path) | Observed-mode fixture parity incl. the 5.323 EOF case |
| 8 | **`.cli` text writer + end-to-end faithful gate** | Output formatting (Fortran FORMAT rounding) | Byte-identical `.cli` files across the fixture matrix; QC subroutines ported and green on both engines |
| A1 | **Provenance + `.cli.parquet`** (SPEC-PROVENANCE, SPEC-CLI-PARQUET) | Generation-profile block; parquet writer with provenance columns | Spec ratified; openWEPP-side consumption is openWEPP's package |
| A2 | **Native f64 mode** | Uniform-f64 engine; measured faithful↔native divergence characterization | Divergence documented per variable; profile `native-f64-v1` |
| A3 | **Observed parquet input + single-pass substitution + leap-year imputation** (SPEC-OBSERVED-INPUT) | f64 parquet observed series; variable replacement in one pass; leap-day handling | Spec + fixtures; kills the flatfile→wepppyo3→flatfile round-trip |
| A4 | **Par database + mutation utilities** | Typed station DB (US/international/PRISM-adjusted collections); provenance-stamped mutation ops (PRISM localization, deltas, scaling) | Mutated pars carry lineage; lineage flows into output provenance |
| A5 | **Storm-model extensions** | Modified duration/intensity derivation; NOAA design-storm curves | Each behind its own versioned generation profile |
| A6 | **PyO3 surface** (SPEC-PYO3) | Python bindings, Arrow zero-copy hand-off | wepppy consumes without flatfiles |

Items 7–8 are the remaining faithful-mode port. A-items are augmentations
and may reorder on demand; A1 is first among them because every later
extension wants the provenance substrate.
