# A10M1 review

Reviewer: Codex
Evidence mode: Mixed
Disposition: ACCEPT

## Findings resolved during execution

- Current USCRN metadata uses nullable `UN` elevation on an excluded test row;
  inventory now preserves it as null.
- The first lattice loop omitted latitude progression; the finite published
  lattice was corrected before role freeze or series access.
- Integer `start`/`end` Daymet parameters were ignored by the live API; the
  documented explicit `years` form now returns the frozen window.
- The live Daymet header uses `dayl (s)` while the guide describes seconds per
  day; source spelling and normalized unit are now separately explicit.
- V1 exposed four cross-frame boundary tiles with opposite roles. The gate was
  not waived; v1 was invalidated and v2 removed all four without role changes
  or climate-value selection.
- V1/v2 initially shared external shard pathnames. Distinct paths now preserve
  both historical hash surfaces.
- Coverage output initially repeated event totals on Daily01 rows; daily event
  count is now null and only Subhourly01 carries event totals.

## Final review

No open P1/P2 findings. The v2 corpus satisfies the M1 source, calendar,
coverage, role, spatial-leakage, firewall, rights, integrity, and resource
gates. V1 remains explicit failed evidence and is not transferable. No
production Rust function changed, no candidate output was accessed, and no GPU
or Slurm resource was used.
