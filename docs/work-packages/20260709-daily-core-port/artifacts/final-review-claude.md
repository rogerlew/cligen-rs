# Stage R2 Final Review — Claude Code

Reviewer: Claude Code (Stage S author; R2 per the package's cross-review
structure), 2026-07-09.
Evidence mode: Ran (independent gate re-runs, capture arithmetic
cross-checks) + Static (targeted source-vs-port reads of the Stage C
units).

## Verdict

**CLOSE — `EXECUTED-COMPLETE`.** All package acceptance criteria are
met on `main` (Stage C/R1 executed on `main` per the new branch
discipline — no reconciliation needed this time); both reviews
dispositioned; no tolerance anywhere on the acceptance surface.

## Gates — re-run independently (Ran, exits direct)

| Gate | Result |
|---|---:|
| `cargo fmt --check` / `clippy -D warnings` / `cargo test` | 0 / 0 / 0 |
| `tap_identity --ignored` (item-3 streams) | 0 |
| `par_state_identity --ignored` (item-4 streams) | 0 |
| `daily_identity --ignored` — standalone units: windg 189,207 / alphb 72,130 / r5monb 24; full cg 189,207; combined day-loop 189,207 days with 72,130 internally-driven alphb calls | 0 |
| `cargo llvm-cov` + `cargo crap --fail-above` (141 functions, none above 30) | 0 |

Arithmetic cross-checks (Ran): the replay totals equal the raw capture
record counts exactly — `grep -c` over all 24 runs gives cg = wg =
189,207, ab = 72,130, r5 = 24; every captured record of every stream
was consumed with zero drops. Per-case, ab record counts equal the
item-3 `dg` stream counts (alphb is dstg's only caller; e.g. 4,822 for
new-meadows-seed0), locking the draw-order oracle end to end.

## Targeted source-vs-port reads (Static)

R2 targeted the Stage C units (R1 independently read the Stage S
spine):

- **`windg`** vs `cligen.f:2020-2119`: direction-search loop exit
  conditions (including the calm fall-through at j = 16 with `j` left
  in `Cbk3State`), the g-interpolation with its j = 1 special case,
  `th` wrap, the in-place `wvl(j,4,mo)` clamp, the Pearson-III cube,
  and the 0.1 floor — all faithful.
- **`alphb`** vs `cligen.f:3817-3895`: `ei`/`ai`/`ajp` (via
  `expf_pinned`), the single `dstg` draw, and the final rescale with
  its exact operand order — faithful. The added `r > 0` assert is a
  documented fail-closed guard consistent with the `day_gen` call
  sites (the Fortran would divide by zero); hemisphere behavior flows
  through `wi(mo)`/station state and is pinned by the jeogla cases in
  the full matrix.
- **`r5monb`** vs `cligen.f:3898-3996`: smoothing wrap, the
  rain-day/`0.0006944` branch, `r25` floor, `f = −1/alog(f)` through
  `logf_pinned`, the `f > 1 ∨ f ≤ 0` guard, and the in-place `wi`
  conversion — faithful (and correctly trusts the live body over the
  unit's stale header comments).
- **The `day_gen` wet-day protocol** vs `cligen.f:3105-3141`
  (re-read from source): normalize `r ≤ 0` to zero, first `alphb` in
  the wet branch, second `alphb` under `iopt ≥ 4` — the harness
  transcription (with fail-loud missing-record panics and an
  ab-exhaustion assertion) matches. R1's finding 3 was the right
  correction to my Stage S one-call summary; the two-call protocol is
  now both recorded and replay-enforced, and the fixture arithmetic
  (ab records = 2 × wet days = dg calls) confirms it.
- **Transcendental adjudication spot-check**: the census numbers match
  my Stage S sweep runs verbatim (I ran those sweeps; 0/24.7M), and
  R1 added the ARM license-file hash verification for `expf_pinned`.

## R1 disposition review

All three findings verified as really fixed: the ignored gates now
enumerate the 24-case `FULL_CASES` matrix (finding 1 — a real gap in
my Stage S test scaffolding, confirmed closed by the 189,207-call
totals above); the stale state/spec prose is corrected
(SPEC-GENERATOR-CORE rev 6, `cbk1.rs`); the wet-day protocol is
characterized and transcribed (finding 3, above). No open findings.

## Observations (accepted, non-blocking)

1. `r5monb`'s `wi(i) = wi(i)/r25` became `bk9.wi[i] /= r25` — the
   compound assignment is bit-identical here; noted only because the
   repo's faithful-shape convention usually keeps the source's
   explicit form.
2. `windg` resets `ndflag` once rather than per loop iteration; the
   source's per-iteration reset is unobservable (the loop exits the
   moment it becomes nonzero) — equivalent, noted for the record.

## Close-out actions

- Package status → `EXECUTED-COMPLETE`.
- ROADMAP item 5 moved to the work-package record.
