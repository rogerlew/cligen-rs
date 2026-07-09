# `ranset(mox = 0)` Characterization

Evidence mode: Static source/layout analysis + Ran 12-fixture capture
(2026-07-09).

## Reachability

Static: the only live `ranset` call is `cligen.f:1204-1209`. Its guarded
month-change branch assigns `mox = mo` at line 1207 immediately before the
call at line 1209. `mo` is the 1-based month produced by `jlt`; no live
production path calls `ranset` while block-data `mox = 0` remains in effect.

Ran: all 2,584 Stage C `ranset` entry records across the 12 fixture commands
captured `mox` in `1..=12`; none captured zero. This includes both
single-storm invocations.

## Source behavior for a direct invalid call

Static: a direct call with `mox = 0` first reads `dim(0)` at
`cligen.f:4091-4095`, one INTEGER before the local `dim(12)` array. Its value
is layout/compiler dependent. If execution continues, the month-zero
`chicnt` references at lines 4211 and 4315 under-run the second dimension of
`chicnt(10,12,20)`.

For the `/random/` common layout in `crandom3.inc:4-19`, column-major offset
analysis gives:

- `chicnt(j,0,1)` aliases the common words immediately before `chicnt`:
  `g_dimp(6..12)` for `j=1..7`, `chi_n` for `j=8`, and `mox` for `j=9`;
- `chicnt(j,0,ichi)` for `ichi=2..20` aliases
  `chicnt(j,12,ichi-1)`.

The earlier `dim(0)` read prevents a deterministic, source-portable value
from being assigned to `dimi`, so reproducing this behavior would require
inventing compiler/storage-layout semantics outside the Fortran source
authority.

## Port decision

Accepted: fail closed. `ranset` asserts `mox in 1..=12` before indexing any
month storage, and the test
`ranset_fails_closed_on_fortran_month_zero_underrun` pins that decision. This
does not change any reachable production trajectory and avoids silently
turning malformed state into unrelated common-block mutation.
