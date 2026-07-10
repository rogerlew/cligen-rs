# SPEC-OBSERVED-INPUT — Observed-Series Input Seam

Status: active (rev 2 — adds the `initial_year` seam required by
SPEC-RUNSPEC's observed `begin_year` derivation)
Surface: the faithful CLIGEN 5.32.3 `.prn` compatibility reader and its
consumption by `day_gen`. The A3 f64 parquet input, substitution, and
leap-day policies remain a future revision and generation-profile surface.

## Producers / consumers

Producers are external observed-weather file builders that emit the legacy
fixed-column `.prn` records; the committed Mt. Wilson and Fish Springs files
are concrete instances. `observed::PrnReader` is the typed parser and
sequential cursor. `modes::day_gen` is the consumer under `iopt = 6`; its
scaled values feed the faithful daily generator and `DailyRow` output seam.

Authority basis: `reference/cligen532/cligen.f:3052` (format
`(15x,3i5)`) and `3067-3083` (read, EOF, sentinel flags, and assignments),
plus the 5.323 stop at `3189`. Fidelity questions are answered from those
lines and the fixture files, not external CLIGEN documentation.

## Record grammar

Each text record has 15 ignored columns followed by three five-column
integer fields:

| Columns | Field | Units and sentinel |
|---|---|---|
| 1-15 | per-day reads: ignored | fixture date columns; not validated or exposed by the daily cursor. **Rev 2**: columns 11-15 of the *first* record are additionally readable once, at open, as `initial_year` — the source's `ioyr` (`usr_opt` reads it with `(10x,i5)` and `backspace`s so the record is not consumed, `cligen.f:3524-3572`). SPEC-RUNSPEC's observed `begin_year` default derives from it; the read is non-consuming and its parse failure is fail-closed like any field. A3's parquet source must expose the same semantic through the common observed-source interface. |
| 16-20 | `irida` | hundredths of an inch precipitation; `9999` means generate |
| 21-25 | `itmxg` | maximum temperature, °F; `9999` means generate |
| 26-30 | `itmng` | minimum temperature, °F; `9999` means generate |

The compatibility reader accepts ASCII text with LF or CRLF record
terminators. CRLF is equivalent because the record terminator is outside
the formatted fields, as it is for the Fortran sequential read.

## Fixed-column read semantics

- Records shorter than column 30 are right-padded with spaces, matching
  Fortran `PAD='YES'`.
- ASCII spaces inside each `I5` field are removed (`BLANK='NULL'`). An
  all-space or entirely padded field is integer zero.
- A nonblank field must parse as an `i32`, including an optional sign.
  Tabs and other non-space characters are not blanks.
- Non-ASCII input returns `PrnError::NotText`; a malformed numeric field
  returns `PrnError::Field` with its 1-based record and column range. No
  value is inferred after either error.
- `PrnReader::next` consumes one record. End-of-file is `Ok(None)`, distinct
  from a blank record, whose three values are zero.

## `day_gen` consumption and stop protocol

For every observed day, source order is normative:

1. Set `msim = 0`, `nsim = 0`.
2. Arm `moveto = 225`; a missing next record therefore returns
   `DayGenExit::Stop` before `jlt`, generation, or grid writes. A successful
   read clears the conceptual `moveto` flag.
3. Set the saved `q_gen_started` flag when `irida == 9999` or
   `itmxg == 9999`. The source deliberately does not include an
   `itmng`-only sentinel in this assignment.
4. Set `nsim = 1` for precipitation sentinel; set `msim = 1` when either
   temperature is a sentinel.
5. Assign every input regardless of sentinel:
   `r(ida) = real(irida) * 0.01`, `tmxg = real(itmxg)`, and
   `tmng = real(itmng)`. These are f32 operations/values in faithful mode.

`DayGenState.q_gen_started` is the explicit caller-owned translation of the
source SAVE variable and persists across yearly calls. At a natural year
end, a true flag also produces `DayGenExit::Stop`; otherwise the result is
`YearComplete`. Calling observed mode without a reader returns the typed
`PrnError::MissingStream` instead of prompting, defaulting, or panicking.

## Precision and extension boundary

Legacy integer fields are converted directly to f32 at the source
assignment sites. Precipitation uses the source literal `0.01`; temperatures
remain Fahrenheit until the later `day_gen` F-to-C seam. Parsing and stop
logic add no transcendental operation and do not widen faithful values.

This revision does not define parquet input, f64 substitution, leap-day
imputation, or mixed observed/generated provenance. Those are A3 behavior
and must arrive behind a declared generation profile in a later spec
revision; they may not silently change this compatibility path.

## Provenance obligations

The legacy `.prn` format carries no internal lineage. Future generated
outputs must identify the input lineage and generation profile through
SPEC-PROVENANCE. The compatibility reader does not synthesize provenance.

## Acceptance

- Edge vectors cover short-record padding, blank-to-zero fields,
  nonnumeric and non-ASCII rejection, LF/CRLF equivalence, and a missing
  observed stream.
- The committed cold-start sample gate reads the real fixture files with no
  captured generator-state injection.
- The ignored release gate reproduces all 189,207 captured days across 24
  cases. Every case pins its exact day count, final `(year, month, day)`, and
  `DayGenExit`; Fish Springs covers both mid-year EOF and sentinel-triggered
  year-end stop behavior.
