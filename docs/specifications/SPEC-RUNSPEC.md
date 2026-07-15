# SPEC-RUNSPEC — The `inp.yaml` Run Specification and `cligen` CLI Surface

Status: active (rev 8 — A8c adds the explicitly paired routed pilot profile;
rev 7 — A1 adds optional `output.parquet`, mandatory text
provenance, and the portable canonical-effective-runspec contract; rev 6 — A4a adds exactly-one `station.par` or
`station.document`, with the station-document version independent of this
runspec revision; rev 5 — `qc_filter: faithful | off` accepted
2026-07-10 by the Q3 package `20260710-q3-qc-filter-dissection`,
schema rev landing with the implementation; rejected with
`fast_batch_v0`. Rev 4 — `output.quality` accepted 2026-07-10 by the
Q1 package `20260710-q1-quality-report`, the schema rev landing with
the implementation per the F3 discipline; rev 3 — `fast_batch_v0`
profile selector added 2026-07-10;
rev 2 contract ratified 2026-07-09, operator
decision; rev 2 dispositions the 13-finding independent review,
`docs/work-packages/20260709-runspec-contract/artifacts/review-codex.md`;
implementation lands with ROADMAP item 8)
Surface: the generation interface of the `cligen` binary: a single
schema-versioned YAML document that fully specifies a run. Auxiliary
`quality` and `stations` subcommands are specified by their owning surfaces.
The legacy
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
- **Versioned**: `cligen_runspec: 1` is required. Compatible additions update
  this contract revision and its published JSON Schema; an incompatible
  envelope change bumps `cligen_runspec`.
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
  par: id106388.par             # exactly one of `par` (SPEC-PAR) or
  # document: id106388.station.json  # `document`
                                # (SPEC-STATION-DOCUMENT). No extension
                                # sniffing. The legacy -S/-s multi-station
                                # scan is excluded — see §Non-goals.

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

qc_filter: faithful             # optional, default faithful (rev 5):
                                # faithful | off — the QC conditioning
                                # policy (SPEC-GENERATION-PROFILES).
                                # `off` appends `--qc-filter off` to the
                                # header echo. REJECTED with
                                # generation_profile fast_batch_v0
                                # (pre-knob, always unconditioned).

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
  parquet: wepp.cli.parquet     # optional A1 companion; continuous or
                                # observed only (SPEC-CLI-PARQUET)
  overwrite: false              # optional, default false (legacy -F;
                                # false = typed error if the file
                                # exists — never a prompt)
  command_echo: "-iid106388.par"  # optional; §Header echo
  quality: true                 # optional, default true: emit the
                                # <output.cli>.quality.json sidecar
                                # (SPEC-QUALITY-REPORT). The sidecar
                                # is always rewritten when enabled;
                                # `overwrite` governs declared .cli and
                                # .cli.parquet climate destinations.
```

## Field invariants (normative; JSON Schema plus semantic validation)

| Field | Type / domain |
|---|---|
| `cligen_runspec` | integer, exactly 1 in this revision |
| `station.par`, `station.document` | exactly one non-empty string path; syntax selected explicitly, never by extension |
| `observed.prn`, `output.cli` | non-empty string paths |
| `output.parquet` | optional non-empty string path ending in `.cli.parquet`; distinct/non-aliasing from text, companions, and reserved staging paths (semantic filesystem check); rejected in storm modes |
| `mode`, `simulation.interpolation` | closed enums as listed |
| `simulation.begin_year` | integer 1–99,999 where accepted |
| `simulation.years` | integer ≥ 1 whose final year is ≤ 99,999 |
| `rng.burn` | integer 0–2,147,483,647 (faithful signed-32-bit control/header domain) |
| `generation_profile` | closed enum: `faithful_5_32_3` (default), `fast_batch_v0`, or the non-default `a8c_routed_daily_v1` pilot (SPEC-GENERATION-PROFILES) |
| `qc_filter` | closed enum: `faithful` (default) or `off` (rev 5); rejected under `generation_profile: fast_batch_v0` |
| `*.date` | month 1..12, day valid for the month under the **source's** calendar rules for the mode; storm year −9,999..99,999 (legacy `i5`) |
| `amount_in`, `duration_h`, `max_intensity_in_per_h` | finite f32-convertible input, > 0 |
| `time_to_peak_fraction` | finite f32-convertible input in (0, 1] |
| `output.command_echo` | base string without NUL/CR/LF; generation always appends required profile/QC markers for divergent behavior |
| `output.overwrite` | boolean |
| `output.quality` | boolean, default true (rev 4) |
| parent blocks (`simulation`, `rng`) | omissible when every member is optional/defaulted; mode-conditional blocks (`observed`, `single_storm`, `design_storm`) required for their mode and **rejected under any other mode** |

`a8c_routed_daily_v1` requires `station.document` revision 2, `mode:
continuous`, interpolation `none`, and `qc_filter: faithful`. It rejects
legacy `.par`, revision-1 documents, observed/storm modes, and implicit route
selection. Conversely, existing profiles reject revision-2 routed documents.

Anything else — unknown fields anywhere, wrong types, out-of-domain
values, or an explicit YAML/JSON `null` where a field type is non-null — is a
typed validation error. Omission alone selects a documented default.
Resolved provenance stores the exact widened f32 values actually consumed by
the generator, not the original higher-precision YAML lexemes.

The draft [`SPEC-FAST-BATCH-V1`](SPEC-FAST-BATCH-V1.md) defines the proposed
successor to the experimental profile and its ADR-0002 quality assessment. It
does not amend this schema: `fast_batch_v1` must fail closed until a
later runspec revision accepts it. The `qc_filter` policy knob
(SPEC-GENERATION-PROFILES) is **accepted as of rev 5** (Q3 implementation),
and the `output.quality` opt-out (SPEC-QUALITY-REPORT) **as of rev 4**
(Q1) — each schema rev landing with its implementation.

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
  lexical runspec fields (order: `-rN`, the station selector, `-O<prn>`,
  `-o<cli>`, `-t<mode>`, `-I<n>`, each only when non-default). The
  legacy selector is `-i<par>`; the modern selector is
  `--station-document=<document>`.
  The canonical order cannot reproduce every historical command line
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
declared inputs** (`.par` via SPEC-PAR or modern JSON via
SPEC-STATION-DOCUMENT, `.prn` via
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
itself** (resolved defaults and lexical paths) together with
its hash **and content identities (hashes) of every input artifact**
(`.par` or station document, `.prn`). A converted station document also
carries its legacy-source SHA-256 per SPEC-STATION-DOCUMENT. A hash alone is
not a substitute for the document,
and provenance *identifies* inputs — reproduction additionally
requires the identified input bytes. Details land in SPEC-PROVENANCE;
this spec fixes what the runspec side must supply.

Resolved filesystem paths remain runtime context and are deliberately absent
from serialized provenance: they leak host/cache layout and are not portable
identity. Exact selected bytes are bound by their hashes. This rev-7 A1 ruling
supersedes rev 6's requirement to serialize both lexical and resolved paths.

Every run writes `<output.cli>.provenance.json`, including when
`output.quality: false`. The optional Parquet artifact embeds the same shared
run identity with its independent output-schema descriptor. `output.overwrite`
governs both declared climate destinations; derived provenance/quality
companions are rewritten to match the newly produced text.
One canonical-destination lock serializes cooperating writers. On success the
publication order is text, mandatory provenance, optional Parquet, then
optional quality. Each non-text artifact is staged and atomically renamed;
the bundle as a whole is not claimed to be transactional. Abrupt process or
host termination may leave the hidden `.cligen-lock` file. After confirming
that no writer is active for that destination, an operator may remove the
stale lock and retry the run.

## Non-goals (ratified)

- **No legacy argv/stdin emulation, ever.** The equivalence table is
  the complete bridge; legacy-interface consumers (GeoWEPP-era
  tooling) are explicitly not a compatibility target (operator
  decision, 2026-07-09). The header echo (§above) is output-byte
  compatibility, not interface emulation.
- **No `-S`/`-s` multi-station catalog selection**: `station.par` remains
  the characterized single-station legacy intake and `station.document` is
  one explicit modern document; the multi-station
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
- Converted modern-station variants of all 12 runspecs reproduce the same
  `.cli` bytes when their explicit historical `command_echo` is retained.
  Quality metrics remain equal while shared provenance truthfully identifies
  the selected station-input schema and bytes.
- Schema/orchestration vectors cover the publicly ratified branches
  the goldens do not reach: `design_storm`, `linear` and
  `monthly_mean_preserving` interpolation, explicit observed
  `begin_year`/`years`, `overwrite: true`, and the canonical
  `command_echo` rendering — labeled fixture-unreachable where no
  golden exists (the established iopt-7 precedent).
