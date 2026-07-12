# Gate results

Date: 2026-07-12
Working tree: `main`

## Repository gates

Ran from the repository root:

```text
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
```

Result: all commands exited 0. The test suite reported 108 passed, 0 failed,
and 9 ignored evidence/long-sweep tests. No production function under
`crates/` changed, so the package does not trigger the `cargo llvm-cov` and
`cargo crap` production-function gates.

## Documentation and source-corpus gates

- Resolved all relative Markdown links in the two literature reviews, package
  artifacts, and `references/` documentation: 8 Markdown files checked, no
  missing local target.
- Compared `references/open-access/manifest.tsv` to the directory: 14 manifest
  rows and 14 PDFs; every computed SHA-256 matched its recorded value.
- Parsed all 14 PDFs with Poppler `pdfinfo`; no invalid file was found.
- Rendered and visually inspected the first page of the two final corpus
  additions, Rglimclim and IMAGE; titles, DOI/article identity, and readable
  page content matched the manifest entries.
- Ran `git diff --check`; no whitespace error was reported.
- Independent reviewers checked faithful-source wording, direct stochastic
  generators, and the subdaily/extreme/ML boundary. Accepted findings and
  corrections are recorded in [`review.md`](review.md).
- DOI resolution and primary-source link checks were completed during source
  acquisition. Papers without independently verified redistribution terms
  remain link-only or under the Git-ignored local reading directory.

Temporary rendered images were removed after visual inspection.

## Local acquisition addendum

After incorporating the local full texts, the three repository commands above
were rerun on 2026-07-12. All exited 0; the result remained 108 passed, 0
failed, and 9 ignored evidence/long-sweep tests.

Additional addendum checks:

- All 10 canonical local-reading rows matched the SHA-256 of the corresponding
  Git-ignored PDF, including context-only AB-39.
- The bibliography contains 39 uniquely numbered annotations; AB-39 has an
  explicit no-DOI note.
- First pages of the 10 incorporated local sources rendered successfully and
  were visually checked as a contact sheet. All local PDFs parsed with Poppler.
- The alternate Katz files are one byte-identical group and the second Wilks
  file is an alternate wrapper of AB-03; none was treated as independent
  evidence or staged.
- Local Markdown links and `git diff --check` passed after the addendum.
- Temporary PDF renders were removed, and no file under
  `references/copyrighted/` is tracked.
