# SPEC-RUNSPEC — The `inp.yaml` Run Specification and `cligen` CLI Surface

Status: active (rev 4 — `output.quality` accepted 2026-07-10 by the
Q1 package `20260710-q1-quality-report`, the schema rev landing with
the implementation per the F3 discipline; rev 3 — `fast_batch_v0`
profile selector added 2026-07-10;
rev 2 contract ratified 2026-07-09, operator
decision; rev 2 dispositions the 13-finding independent review,
`docs/work-packages/20260709-runspec-contract/artifacts/review-codex.md`;
implementation lands with ROADMAP item 8)
Surface: the **only** user interface of the `cligen` binary: a single
schema-versioned YAML document that fully specifies a run. The legacy
CLIGEN interface (argv flags, stdin answer scripts, interactive
prompts) is **deliberately not replicated** — see §Non-goals.

## Producers / consumers

Producers: humans and orchestrators (wepppy writes a runspec instead
of composing argv + stdin scripts; the A6 PyO3 surface constructs the
same typed struct directly, supplying **already-resolved paths** —
§Path resolution). Consumers: the `cligen` binary (`run`/`validate`),
the item-8 byte-parity gate, and the A1 provenance block.

Authority basis: the typed intake surfaces the port ratified
(`StaDatSelection`, `SingleStormParams`, `sing_stm`, `PrnReader`,
`generation_setup`, `day_gen`) and the characterized legacy option
semantics (`cligen.f:645-835` argv parsing; the intake/sing_stm/
day_gen characterizations in the item-4/6/7 packages). Where the
legacy interface's *names* were misleading, this schema renames and
the mapping tables below are normative.

## Design rules

- **One document = one run.** No interactive fallbacks, no cwd-implied
  inputs, no stdin.
- **Fail closed**: unknown fields rejected at every level; missing
  mode-conditional blocks are typed errors; only schema-declared
  defaults exist (each cites the legacy behavior it preserves).
  Numeric domains are the **legacy-permissive** ones (§Field
  invariants) — the schema types and bounds what the source would
  crash or misbehave on, and does not invent physical limits the
  source never enforced.
- **Versioned**: `cligen_runspec: 1` is required; future revisions
  bump it. A published JSON Schema accompanies the implementation.
- **Faithful semantics, honest names** (§Naming traps).

Machine-readable schema: [`runspec.schema.json`](runspec.schema.json).

## Path resolution (API boundary)

Relative paths in a runspec **file** resolve against the file's
directory. Resolution is an explicit API boundary: the typed loader
takes `(document, base_dir)`; in-memory constructors (A6 PyO3) supply
already-resolved paths and no base directory exists. Both the lexical
(as-written) and resolved forms are retained — the lexical forms feed
the faithful header echo (§Header echo) and A1 provenance.

## Schema (version 1)

```yaml
cligen_runspec: 1               # required

station:
  par: id106388.par             # required; the single-station .par
                                # intake (SPEC-PAR). The legacy -S/-s
                                # multi-station scan is excluded — see
                                # §Non-goals.

mode: continuous                # required:
                                # continuous | observed | single_storm
                                # | design_storm
                                # (legacy iopt 5 | 6 | 4 | 7)

simulation:                     # block optional for observed and the
                                # storm modes (see the year-plan table)
  begin_year: 1                 # continuous: required (legacy -b /
                                #   prompt); a YEAR INDEX (§Year plan)
                                # observed: optional — default derives
                                #   from the observed record's first
                                #   year (§Year plan)
                                # storm modes: REJECTED (the storm date
                                #   carries the year)
  years: 31                     # continuous: required (legacy -y)
                                # observed: optional, default 100 — a
                                #   CAP on year loops; the run ends at
                                #   the earlier of the cap or the stop
                                #   protocol (§Year plan)
                                # storm modes: REJECTED (exactly one
                                #   generation pass; the faithful
                                #   header still echoes the legacy
                                #   numyr = -1 — §Header echo)
  interpolation: none           # optional, default none:
                                # none | linear | fourier
                                # | monthly_mean_preserving
                                # (legacy -I0..-I3)

rng:                            # block optional
  burn: 0                       # optional, default 0. The legacy -rN
                                # semantics named honestly: N discarded
                                # draws from EACH of k1..k9 (9N draws
                                # total); k10 is unchanged
                                # (cligen.f:723-737). NOT a seed value;
                                # the base seeds are the fixed
                                # block-data constants.

generation_profile: faithful_5_32_3  # optional, default. See
                                      # SPEC-GENERATION-PROFILES.
                                      # `fast_batch_v0` is an explicit,
                                      # non-faithful experimental profile.
                                      # `fast_batch_v1` is a draft only and
                                      # is rejected in this revision.

observed:                       # required iff mode: observed
  prn: ws.prn                   # the observed series
                                # (SPEC-OBSERVED-INPUT; A3 adds a
                                # parquet alternative as a sibling
                                # field — exactly one source required)

single_storm:                   # required iff mode: single_storm
  date: { month: 6, day: 15, year: 12 }   # year = the run's iyear
  amount_in: 2.25               # damt, inches
  duration_h: 6.0               # usdur, hours
  time_to_peak_fraction: 0.4    # ustpr
  max_intensity_in_per_h: 1.5   # uxmav

design_storm:                   # required iff mode: design_storm
  date: { month: 6, day: 15, year: 12 }
  amount_in: 2.25               # duration fixed 24 h; peak shape from
                                # the station TYPE via dtp/tymax

output:
  cli: wepp.cli                 # required; the .cli destination
                                # (SPEC-CLI-PARQUET adds parquet)
  overwrite: false              # optional, default false (legacy -F;
                                # false = typed error if the file
                                # exists — never a prompt)
  command_echo: "-iid106388.par"  # optional; §Header echo
  quality: true                 # optional, default true: emit the
                                # <output.cli>.quality.json sidecar
                                # (SPEC-QUALITY-REPORT). The sidecar
                                # is always rewritten when enabled;
                                # `overwrite` governs the .cli only.
```

## Field invariants (normative; encoded in the JSON Schema)

| Field | Type / domain |
|---|---|
| `cligen_runspec` | integer, exactly 1 in this revision |
| `station.par`, `observed.prn`, `output.cli` | non-empty string paths |
| `mode`, `simulation.interpolation` | closed enums as listed |
| `simulation.begin_year` | integer ≥ 1 where accepted |
| `simulation.years` | integer ≥ 1 where accepted |
| `rng.burn` | integer ≥ 0 |
| `generation_profile` | closed enum: `faithful_5_32_3` (default) or the explicitly labeled extension `fast_batch_v0` (SPEC-GENERATION-PROFILES) |
| `*.date` | month 1..12, day valid for the month under the **source's** calendar rules for the mode (§Year plan; validated before `jdt` so no assertion is reachable) |
| `amount_in`, `duration_h`, `max_intensity_in_per_h` | finite f32-convertible, > 0 |
| `time_to_peak_fraction` | finite f32-convertible in (0, 1] |
| `output.overwrite` | boolean |
| `output.quality` | boolean, default true (rev 4) |
| parent blocks (`simulation`, `rng`) | omissible when every member is optional/defaulted; mode-conditional blocks (`observed`, `single_storm`, `design_storm`) required for their mode and **rejected under any other mode** |

Anything else — unknown fields anywhere, wrong types, out-of-domain
values — is a typed validation error.

The draft [`SPEC-FAST-BATCH-V1`](SPEC-FAST-BATCH-V1.md) defines the proposed
successor to the experimental profile and its ADR-0002 quality assessment. It
does not amend this schema: `fast_batch_v1` must fail closed until a
later runspec revision accepts it. The same holds for the `qc_filter` policy
knob (SPEC-GENERATION-PROFILES rev 3): a declared contract, rejected by this
schema revision until the Q3 implementation package accepts it. The
`output.quality` opt-out (SPEC-QUALITY-REPORT) is **accepted as of rev 4**,
its schema rev landing with the Q1 implementation.

## Year plan (normative, per mode)

| Mode | `iyear` source | Year count | Leap rule |
|---|---|---|---|
| continuous | `simulation.begin_year` — a **year index**, not a calendar year | `simulation.years`, exact | Gregorian test applied to the index (`wxr_gen:3770-3772`): index 4 is leap |
| observed | `simulation.begin_year`, defaulting to the observed record's first year (`initial_year`, columns 11-15 of the first record — SPEC-OBSERVED-INPUT rev 2; the read does not consume the record) | `simulation.years` (default 100) as a **cap**; the run ends at the earlier of the cap or the stop protocol — mid-year on hard EOF, after the completed year on the sentinel-triggered `q_gen_started` stop | Gregorian on the (calendar) year |
| single_storm / design_storm | `single_storm.date.year` / `design_storm.date.year` — the date's year **is** `ibyear`/`iyear` (`cligen.f:3384-3419`); `simulation.begin_year`/`years` are rejected | exactly one generation pass | the source's **distinct iopt-4/7 `nt` test** (`wxr_gen:3758-3763` — note its `.and.` where the daily rule has `.and..not.`), transcribed, not the Gregorian rule |

## Header echo (`.cli` byte surface)

The legacy binary writes the accumulated argv string into the `.cli`
station-header row (`arg_v`, built at `cligen.f:665-683`, emitted by
`wxr_gen`), and the goldens carry it byte-for-byte — including flag
order, lexical path spellings, omissions, and trailing whitespace.
This is **output surface, not input emulation**:

- `output.command_echo` (optional string) is emitted verbatim in that
  header field.
- When omitted, the implementation renders a canonical echo from the
  lexical runspec fields (order: `-rN`, `-i<par>`, `-O<prn>`,
  `-o<cli>`, `-t<mode>`, `-I<n>`, each only when non-default). The
  canonical order cannot reproduce every historical command line
  (the goldens themselves differ in flag order), which is exactly why
  the explicit field exists.
- The golden runspecs pin `command_echo` verbatim from
  `fixture-runs.tsv`; byte parity is asserted on the whole file.
- Non-faithful profiles append their mandatory profile marker after this
  echo; an explicit `command_echo` cannot suppress it. Faithful output keeps
  its legacy-compatible bytes.

The legacy header also echoes `numyr` as `-1` for storm modes and
`100` for defaulted observed runs — the faithful writer reproduces
the *legacy-visible* values, not the schema's resolved ones (the
resolved values are provenance surface).

## Legacy naming traps this schema fixes (normative)

| Legacy | Trap | Schema |
|---|---|---|
| `-rN` "random seed" | a **burn count**: N draws from each of `k1..k9` (9N total), `k10` excluded (`cligen.f:723-737`); base seeds are fixed block-data constants | `rng.burn` |
| `-b`/`iyear` | a year **index** in continuous mode, leap rule applied to the index; storm modes take the year from the storm date and ignore `-b` | `simulation.begin_year` / `date.year` per the year-plan table |
| `-H`/`dohedr` | **behaviorally dead**: written (`cligen.f:765,962,1088`) but never read; the header is written unconditionally | no field; ratified inert (a future header-suppression option would be a labeled extension, not `-H` semantics) |
| `itype` | station data (the `.par` `TYPE=` field, record 2) feeding `tymax`/`dtp` — never a CLI concern | absent |
| `-t1..3`, `-t8` | screen/CREAMS display modes and the interactive exit — not run identity | excluded (§Non-goals) |
| `-v/-V`, `-h/-?` | version/help printers | not replicated; the new CLI has conventional `--version`/`--help` of its own |
| prompts, stdin scripts, overwrite dialog | run identity smeared across argv + stdin + tty | the document is the run; `output.overwrite` is a boolean |

## `validate` vs `run` (normative)

Both commands: parse the YAML, enforce the schema and mode-conditional
rules, resolve paths against the base directory, **open and parse the
declared inputs** (`.par` via SPEC-PAR, `.prn` via
SPEC-OBSERVED-INPUT — including the observed `initial_year`
derivation), and resolve effective defaults. `validate` performs no
generation and never creates, truncates, or stats the output path —
output-collision checking is deliberately excluded so validation is
deterministic across workspaces. `run` additionally enforces the
overwrite policy and generates.

## Golden equivalence table (normative examples)

The 12 golden fixtures map to runspec documents as follows; each
golden runspec also pins `output.command_echo` verbatim from
`fixture-runs.tsv`. The item-8 acceptance is `cligen run <spec>`
reproducing each golden `.cli` byte-identically.

| Golden | Legacy invocation | Runspec |
|---|---|---|
| new-meadows-id-seed0 | `-iid106388.par` + stdin `5,1,31,wepp.cli,n` | continuous; begin_year 1; years 31; interpolation none; burn 0 |
| new-meadows-id-seed17 | `-r17 -iid106388.par` + same stdin | same + `rng.burn: 17` |
| jeogla-au-seed0 / -seed17 | `-iASN00057011.par` + stdin `5,1,42,…` | continuous; years 42; burn 0 / 17 |
| mt-wilson-ca-observed ×2 | `-ica046006.par -Ows.prn -owepp.cli -t6 -I2` | observed; prn ws.prn; interpolation fourier; begin_year/years omitted (derive 1990 / cap 100); burn 0 / 17 |
| fish-springs padded ×2 | `-iut422852.par -Ows.prn … -t6 -I2` | as mt-wilson, station ut422852 |
| fish-springs truncated ×2 | `… -Ows-truncated.prn …` | as above, `observed.prn: ws-truncated.prn` |
| new-meadows single-storm ×2 | `-iid106388.par -t4 -owepp.cli` + stdin `6 15 12 / 2.25 / 6.0 / 0.4 / 1.5` | single_storm with the §Schema block — **no `simulation` block**; the date carries year 12; burn 0 / 17 |

## Provenance obligations

The A1 provenance block embeds the **canonical effective runspec
itself** (resolved defaults, lexical + resolved paths) together with
its hash **and content identities (hashes) of every input artifact**
(`.par`, `.prn`). A hash alone is not a substitute for the document,
and provenance *identifies* inputs — reproduction additionally
requires the identified input bytes. Details land in SPEC-PROVENANCE;
this spec fixes what the runspec side must supply.

## Non-goals (ratified)

- **No legacy argv/stdin emulation, ever.** The equivalence table is
  the complete bridge; legacy-interface consumers (GeoWEPP-era
  tooling) are explicitly not a compatibility target (operator
  decision, 2026-07-09). The header echo (§above) is output-byte
  compatibility, not interface emulation.
- **No `-S`/`-s` multi-station catalog selection**: `station.par` is
  the characterized single-station intake only; the multi-station
  scan path remains excluded exactly as SPEC-PAR defers it. No
  silent first-station fallback.
- No interactive mode; legacy `iopt` 1-3 and 8 not exposed; `-v/-h`
  replaced by conventional CLI conventions (traps table).

## Acceptance (lands with item 8)

- `cligen validate` accepts the 12 golden runspecs and rejects
  unknown-field / missing-block / wrong-mode-block / out-of-domain
  mutations of each (fail-closed vectors per §Field invariants).
- `cligen run` on the 12 golden runspecs reproduces the 12 golden
  `.cli` files byte-identically — including the header echo.
- Schema/orchestration vectors cover the publicly ratified branches
  the goldens do not reach: `design_storm`, `linear` and
  `monthly_mean_preserving` interpolation, explicit observed
  `begin_year`/`years`, `overwrite: true`, and the canonical
  `command_echo` rendering — labeled fixture-unreachable where no
  golden exists (the established iopt-7 precedent).
