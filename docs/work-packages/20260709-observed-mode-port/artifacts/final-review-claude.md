# Stage R2 Final Review — Claude Code

Reviewer: Claude Code (Stage S author; R2 per the cross-review
structure), 2026-07-09.
Evidence mode: Ran (independent gate re-runs, code verification of R1
fixes) + Static (R1 disposition review).

## Verdict

**CLOSE — `EXECUTED-COMPLETE`.** All acceptance criteria met on
`main`; both reviews dispositioned; no tolerance anywhere.

## Gates — re-run independently (Ran, exits direct)

fmt / clippy / test: 0. All five `--ignored` release suites: 0,
including the **cold-start full matrix: 189,207 days across all 24
captures with zero injected state** and per-case endpoint/exit
assertions. Coverage + CRAP: 0 (156 functions, none above 30;
`day_gen` at 19.0).

## R1 disposition review

All four Medium findings verified fixed in code (Ran: grep/read):

1. `generation_setup` now writes `bk4.nt = 0` at the source-order
   point (`cligen.f:881`) with a regression starting from `nt = 1` —
   a real transcription omission in my Stage S function, masked by
   default construction; the public-surface argument is correct.
2. Missing observed stream returns typed `PrnError::MissingStream`
   before any generation, replacing my `expect` panic — the
   fail-closed posture applied to my own code.
3. SPEC-OBSERVED-INPUT authored and active (and already extended to
   rev 2 by the runspec review's `initial_year` seam);
   SPEC-GENERATOR-CORE rev 8 records the `modes` ownership and the
   `DailyRow` seam — the contract-first rule enforced against the
   spine.
4. The cold-start evidence wording corrected: the modes gate compares
   the complete reconstructed `DailyRow` stream; the finer per-record
   internal assertions live in the earlier unit suites — the
   truthfulness discipline applied to my acceptance header.

Findings 1 and 4 were defects in the Stage S spine — the cross-review
structure working exactly as designed, in both directions.

## Close-out

Package → `EXECUTED-COMPLETE`; ROADMAP item 7 moved to the record.
**Item 8 is the last faithful-mode item**: `wxr_gen`/`opt_calc`
orchestration, the `.cli` writer (FORMAT rounding + the header echo
per SPEC-RUNSPEC rev 2), and the `cligen` binary whose gate is the 12
golden runspecs reproducing the golden bytes.
