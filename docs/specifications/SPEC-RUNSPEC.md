# SPEC-RUNSPEC — The `inp.yaml` Run Specification and `cligen` CLI Surface

Status: active (rev 1 — contract ratified 2026-07-09, operator
decision; implementation lands with ROADMAP item 8)
Surface: the **only** user interface of the `cligen` binary: a single
schema-versioned YAML document that fully specifies a run. The legacy
CLIGEN interface (argv flags, stdin answer scripts, interactive
prompts) is **deliberately not replicated** — see §Non-goals.

## Producers / consumers

Producers: humans and orchestrators (wepppy writes a runspec instead
of composing argv + stdin scripts; the A6 PyO3 surface constructs the
same typed struct directly). Consumers: the `cligen` binary
(`run`/`validate`), the item-8 byte-parity gate, and the A1 provenance
block (which embeds the runspec — the run specification and the output
lineage are the same object).

Authority basis: the typed intake surfaces the port already ratified
(`StaDatSelection`, `SingleStormParams`, `sing_stm`, `PrnReader`,
`generation_setup`) and the characterized legacy option semantics
(`cligen.f:645-835` argv parsing; the intake/sing_stm
characterizations in the item-4/6/7 packages). Where the legacy
interface's *names* were misleading, this schema renames and the
mapping table below is normative.

## Design rules

- **One document = one run.** No interactive fallbacks, no cwd-implied
  inputs, no stdin. Paths are resolved relative to the runspec file's
  directory.
- **Fail closed**: unknown fields are rejected; missing
  mode-conditional blocks are typed errors; only schema-declared
  defaults exist (each cites the legacy behavior it preserves).
- **Versioned**: `cligen_runspec: 1` is required; future revisions
  bump it. A published JSON Schema accompanies the implementation.
- **Faithful semantics, honest names**: the schema fixes legacy naming
  traps without changing behavior (see the trap table).

## Schema (version 1)

```yaml
cligen_runspec: 1               # required

station:
  par: id106388.par             # required; the .par station file
                                # (.par.yaml later, per the flat-file
                                # modernization plan)

mode: continuous                # required:
                                # continuous | observed | single_storm
                                # | design_storm
                                # (legacy iopt 5 | 6 | 4 | 7)

simulation:
  begin_year: 1                 # continuous/single_storm/design_storm:
                                #   required (legacy -b / prompt)
                                # observed: optional — default derives
                                #   from the observed record exactly as
                                #   legacy ibyear = -1 -> ioyr
  years: 31                     # continuous: required (legacy -y)
                                # observed: optional — default 100
                                #   (legacy numyr = -1 -> 100; the run
                                #   ends at record end regardless)
                                # single/design storm: fixed 1, field
                                #   rejected if present
  interpolation: none           # optional, default none:
                                # none | linear | fourier
                                # | monthly_mean_preserving
                                # (legacy -I0..-I3)

rng:
  burn: 0                       # optional, default 0. The legacy -rN
                                # semantics named honestly: N discarded
                                # draws from streams k1..k9 (k10
                                # excluded), on top of the fixed
                                # block-data seeds. NOT a seed value.

observed:                       # required iff mode: observed
  prn: ws.prn                   # the observed series (A3 adds a
                                # parquet alternative here)

single_storm:                   # required iff mode: single_storm
  date: { month: 6, day: 15, year: 12 }
  amount_in: 2.25               # damt, inches
  duration_h: 6.0               # usdur, hours
  time_to_peak_fraction: 0.4    # ustpr
  max_intensity_in_per_h: 1.5   # uxmav

design_storm:                   # required iff mode: design_storm
  date: { month: 6, day: 15, year: 12 }
  amount_in: 2.25               # duration is fixed 24 h; peak shape
                                # comes from the station TYPE via
                                # dtp/tymax (see trap table)

output:
  cli: wepp.cli                 # required; the .cli destination
                                # (SPEC-CLI-PARQUET adds parquet)
  overwrite: false              # optional, default false (legacy -F;
                                # false = error if the file exists —
                                # never a prompt)
  header: true                  # optional, default true (legacy -H
                                # sets false; the dohedr WEPS header
                                # switch)
```

## Legacy naming traps this schema fixes (normative)

| Legacy | Trap | Schema |
|---|---|---|
| `-rN` "random seed" | It is a **burn count** — N discarded draws from `k1..k9` (`cligen.f:723-737`), `k10` excluded; base seeds are fixed block-data constants | `rng.burn` |
| `iyear`/`-b` | In stochastic modes the year is an **index**, and the leap rule applies to the index (year 4 is leap; `wxr_gen:3770-3772`) | documented on `simulation.begin_year`; a native-mode profile may add calendar dates later |
| `itype` | Never a CLI concern — it is station data (the `TYPE=` field of the `.par`, record 2) feeding `tymax`/`dtp` | absent from the schema |
| `-t1..3` | Screen-summary / CREAMS output modes — display-era surfaces the port defers fail-closed throughout | excluded (§Non-goals) |
| interactive prompts, stdin scripts, overwrite dialog | run identity smeared across argv + stdin + tty | the document is the whole run; `output.overwrite` is a boolean, never a question |

## Golden equivalence table (normative examples)

The 12 golden fixtures map to runspec documents as follows; the item-8
acceptance is `cligen run <spec>` reproducing each golden `.cli`
byte-identically. (Legacy stdin scripts shown for provenance; they
have no runspec counterpart because their content becomes fields.)

| Golden | Legacy invocation | Runspec |
|---|---|---|
| new-meadows-id-seed0 | `-iid106388.par` + stdin `5,1,31,wepp.cli,n` | mode continuous; begin_year 1; years 31; interpolation none; burn 0 |
| new-meadows-id-seed17 | `-r17 -iid106388.par` + same stdin | same + `rng.burn: 17` |
| jeogla-au-seed0 / -seed17 | `-iASN00057011.par` + stdin `5,1,42,…` | mode continuous; years 42; burn 0 / 17 |
| mt-wilson-ca-observed-seed0 / -seed17 | `-ica046006.par -Ows.prn -owepp.cli -t6 -I2` | mode observed; observed.prn ws.prn; interpolation fourier; begin_year/years omitted (derived); burn 0 / 17 |
| fish-springs padded ×2 | `-iut422852.par -Ows.prn … -t6 -I2` | as mt-wilson, station ut422852 |
| fish-springs truncated ×2 | `… -Ows-truncated.prn …` | as above, `observed.prn: ws-truncated.prn` |
| new-meadows single-storm ×2 | `-iid106388.par -t4 -owepp.cli` + stdin `6 15 12 / 2.25 / 6.0 / 0.4 / 1.5` | mode single_storm with the block shown in §Schema; burn 0 / 17 |

## Provenance obligations

The A1 provenance block embeds the resolved runspec (or its canonical
hash) plus the effective defaults, the generation profile, and the
station lineage — a `.cli`/parquet output is reproducible from its own
provenance alone.

## Non-goals (ratified)

- **No legacy argv/stdin emulation, ever.** The equivalence table
  above is the complete bridge; external legacy-interface consumers
  (GeoWEPP-era tooling) are explicitly not a compatibility target
  (operator decision, 2026-07-09).
- No interactive mode. Every legacy prompt surface remains a typed
  error in the library and has a field here instead.
- Legacy `iopt` 1-3 output modes are not exposed. If CREAMS output is
  ever wanted it arrives as a labeled extension with its own spec.

## Acceptance (lands with item 8)

- `cligen validate` accepts the 12 golden runspecs and rejects
  unknown-field/missing-block mutations of each (fail-closed tests).
- `cligen run` on the 12 golden runspecs reproduces the 12 golden
  `.cli` files byte-identically — the port's end-to-end gate runs
  through the *new* interface, proving the old bytes.
