# Par Round-Trip Adjudication

Evidence mode: Static format census over the four fixture `.par` files
(commands inline below; re-runnable). The Rust round-trip gate supplies
the Ran evidence once the parser lands (recorded in gate-results.md).

## Question (package acceptance, spine decision)

Can typed-par parse → serialize reproduce the four fixture `.par` files
byte-identically?

## Adjudication

**Split verdict, pinned as follows:**

1. **From typed values alone (a canonical formatter): unreachable.**
   The corpus embeds at least two distinct number-rendering conventions
   — *between* files and *between sections of one file* — so no single
   value→text function can reproduce all four byte streams.
2. **From the typed model as designed (typed values + retained raw
   records): reachable, and gated.** `ParFile::to_bytes()` must equal
   the input bytes for all four fixtures (`par_roundtrip_fixture_bytes`
   test). This is not a vacuous invariant: parse fully validates and
   types the read surface, and the A4 mutation model (below) keeps byte
   stability for every untouched record.
3. **Semantic fixpoint (specified now, for A4):** re-parsing a
   canonically re-rendered record yields the same typed values —
   `parse(canonical(v)) == v` for every field family. SPEC-PAR defines
   the canonical form; the spine pins the invariant so A4 cannot weaken
   it silently.

## Evidence

### Two zero conventions, one corpus

Values in (−1, 1) are written both with a suppressed leading zero
("USDA bare-dot") and with a leading zero:

```
$ for f in */[a-z]*.par; do echo "$f: $(grep -o ' 0\.[0-9][0-9]' $f | wc -l) leading-zero, $(grep -o '  \.[0-9][0-9]' $f | wc -l) bare-dot"; done
fish-springs-ut/ut422852.par:   0 leading-zero, 219 bare-dot
jeogla-au/ASN00057011.par:    185 leading-zero,  73 bare-dot
mt-wilson-ca/ca046006.par:      0 leading-zero, 220 bare-dot
new-meadows-id/id106388.par:    0 leading-zero, 222 bare-dot
```

Jeogla mixes the two **within one file, by section**: its 14 monthly
header rows (records 4–17) are bare-dot (` MX .5 P  1.24   .94 …`)
while its 64 wind records are uniformly leading-zero
(`SKEW      0.89  0.76 …`; zero bare-dot instances in records 18–81).
The USDA files are bare-dot throughout. The corpus therefore comes from
(at least) two producers — the USDA station database and the
wepppy/GHCN builder — and a faithful serializer would have to know
which producer wrote each *section*. That is presentation state, not
station data: storing it as typed fields would be lexeme preservation
wearing a costume.

### Per-row decimal conventions vary

Within the fixed monthly rows alone: `SOL.RAD  529.` (0 decimals,
trailing point), `SD SOL  132.4` (1 decimal), `MEAN P .52`/`DEW PT
56.14` (2), `Time Pk .070` (3). All are read by the same `(8x,12f6.2)`
/ `(8x,12f6.3)` formats (explicit decimal points override the format's
scale), so the typed values do not record which rendering their row
used.

### Structure differs where CLIGEN never reads

- Record 1: USDA files are 49 chars with state/station/igcode codes in
  cols 42–49; jeogla is 80 chars, cols 42+ blank (parsed as zeros).
- The post-CALM tail (never read except its first record — see
  intake-path-characterization.md): 11 lines with four station-weight
  groups in the USDA files, 5 lines with one group in jeogla; jeogla
  pads every line to 80 chars, the USDA files leave tail lines ragged
  (lengths 1/19/23/24/39/79).

Line-length distributions (`awk '{print length($0)}' f | sort -n |
uniq -c`): USDA files: 82 lines of 80 (the data records are exactly
8 + 12×6 = 80 wide) plus 11 ragged; jeogla: 85 of 80 plus one 39 and
one 45. All files LF-terminated, final newline present, no CR.

### What is stable across the corpus

The 14 monthly-row labels (cols 1–8) are byte-identical across all four
files (` MEAN P `, ` S DEV P`, ` SKEW  P`, ` P(W/W) `, ` P(W/D) `,
` TMAX AV`, ` TMIN AV`, ` SD TMAX`, ` SD TMIN`, ` SOL.RAD`, ` SD SOL `,
` MX .5 P`, ` DEW PT `, `Time Pk `), as is the record grammar itself
(3 header records, 14 monthly records, 64 wind records, CALM, tail).
The typed model can therefore validate labels while still retaining
raw bytes for emission.

## Design consequence (SPEC-PAR)

`ParFile` = typed read-surface + retained raw records:

- **Parse** replicates the Fortran fixed-column reads (formats at
  `cligen.f:2753-2756`, first record `(a41,i2,i4,i2)` at 2324) and
  fails closed on grammar violations; typed values are exactly what
  `sta_parms`/`sta_dat` consume.
- **`to_bytes()`** emits the retained records verbatim → byte-identical
  round-trip for unmutated files (the gate).
- **Mutation (A4)** rewrites only the mutated record, using the
  canonical rendering SPEC-PAR defines (bare-dot USDA convention),
  and must satisfy the semantic fixpoint. Untouched records keep their
  bytes. The spine ships parse + `to_bytes` + the gate; the canonical
  renderer is SPEC-PAR-specified surface for A4 (no implementation
  debt taken now beyond the spec).

## Ran evidence

**IN FLIGHT** — filled by gate-results.md when
`par_roundtrip_fixture_bytes` runs against all four fixtures.
