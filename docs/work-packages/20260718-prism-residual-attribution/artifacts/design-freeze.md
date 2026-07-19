# Design freeze

The audit separates three classes of record:

1. **Current authority:** files at `HEAD`, Cargo crate contents, generated
   outputs, and current release assets. These must contain only the canonical
   three-stage pedigree.
2. **Superseded history:** the earlier commit corrected forward by `4af0470`.
   It remains reachable for auditability but has no current semantic authority.
3. **Unrelated scholarship:** same-surname authors outside the PRISM comparator
   authority surface. These are neither evidence for this comparator nor audit
   findings and remain untouched.

The two prohibited identifiers are stored only as lowercase length/SHA-256
fingerprints. The verifier hashes candidate word and DOI tokens on frozen
surfaces, so the regression control does not itself republish the attribution.

No climate method, data bundle, acquisition behavior, profile identity, or git
history changes are in scope. A clean audit closes as documentary hardening;
only a current/public residual authorizes a bounded content correction.
