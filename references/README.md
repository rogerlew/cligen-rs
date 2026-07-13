# Literature references

This directory contains literature used to evaluate proposed `cligen-rs`
extensions. It is **not** an authority for faithful CLIGEN behavior. The
faithful-mode authority remains `reference/cligen532/cligen.f` under ADR-0001.

- `open-access/` contains unchanged article PDFs whose redistribution terms
  were verified before inclusion. Its manifest records the exact source,
  license, retrieval date, and SHA-256 identity of every file.
- `copyrighted/` is reserved for local reading copies that the repository does
  not redistribute and is ignored by Git. Most lack independently verified
  reuse terms; some remain local by operator choice despite verified public
  access. Their access status is recorded per bibliography entry.
- `observed/a5a-v1/` contains the exact Daymet V4 R1 and GHCN-Daily source
  objects used by the independently versioned A5 observed-target corpus.
  Daymet CSVs are deterministically gzip-compressed; GHCN gzip payloads are
  retained byte-for-byte. Source URLs, DOI/version labels, byte and logical
  hashes, fixed periods, and rebuild tooling are recorded in the A5a work
  package. These are evaluation data, never faithful-model authority.

The repository's annotations are original summaries. They do not replace the
papers and do not imply endorsement by their authors.
