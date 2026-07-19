# Design freeze

This package changes provenance visibility only. The profile remains
`stochastic_prism_localized_par_v1`; the PRISM bundle, query cell, station
selector, six-row localization, occurrence algebra, intensity clamp, faithful
generator, and output climate bytes are frozen unchanged.

Every successful `cligen prism run` gains one canonical `method.json`. The
existing artifact-manifest enumeration hashes it automatically. The record's
identity is its exact bytes plus `method_id`; this package does not rename the
generation profile because preprocessing behavior does not change.

Pedigree is layered rather than collapsed:

1. FSWEPP/Rock:Clime originated the PRISM-assisted custom-CLIGEN climate
   concept and the station lineage.
2. WEPPcloud/`wepppy` automated point localization and introduced the exact
   reviewed wet-day and intensity heuristics over time.
3. cligen-rs independently implements a corrected, hash-pinned, local-only
   revision with different selector axes and strict provenance.

None of these layers is described as behavior-identical to another. The
limitations are part of the public method record, not merely an A10 research
note.

An initially misassigned publication branch was removed by operator correction
before any output from the changed mode was generated.
