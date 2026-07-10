# Stage R2 Final Review — Claude Code

Reviewer: Claude Code (Stage S author; R2 per the cross-review
structure), 2026-07-09.
Evidence mode: Ran (independent gate re-runs, capture arithmetic) +
Static (targeted source-vs-port read of the Stage C intake).

## Verdict

**CLOSE — `EXECUTED-COMPLETE`.** All acceptance criteria met on
`main`; both reviews dispositioned; no tolerance anywhere.

## Gates — re-run independently (Ran, exits direct)

fmt / clippy / test: 0. All four `--ignored` release suites: 0. The
full storm replay covers **189,207 days + 36,065 timepk calls** across
all 24 capture runs — equal to the raw capture record counts exactly
(re-counted from the tap files; zero drops). Coverage + CRAP: 0
(148 functions, none above 30).

Arithmetic locks: 36,065 timepk calls = 72,130 alphb calls / 2 (one
timepk vs two alphb per wet day, `day_gen:3114-3141`), closing the
draw-count identity across the item-5 and item-6 captures.

## Targeted source-vs-port read (Static)

`sing_stm` typed intake vs `cligen.f:3325-3421`: all five mode
branches faithful — `iopt = 1` assigns nothing; 4/7 take the typed
storm parameters and keep the **`mo` write into `Cbk4State`**; 6
applies the exact `-1` defaults (`ibyear = ioyr`, `numyr = 100`);
2/3/5 defer to `InteractiveOnly` exactly where the source prompts.
The filename prompt loop and unit-7/8 open/rewind/overwrite protocol
are explicit typed deferrals (the `sta_name` treatment), correctly
leaving filesystem policy to the CLI/output layer. The `iopt = 7`
constructed-vector tests are properly labeled as fixture-unreachable
coverage.

## R1 disposition review

One Low finding (stale "single writer" claim on `/bk4/::mo` after
`sing_stm`'s writer landed) — verified fixed in the `cbk4.rs`
glossary; a real documentation-ownership catch.

## Close-out actions

Package → `EXECUTED-COMPLETE`; ROADMAP item 6 moved to the
work-package record. Items 7 (observed mode) and 8 (`.cli` writer +
end-to-end byte parity) remain; the storm-day tap seam this package
pinned is item 8's daily-row input surface.
