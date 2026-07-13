# A5a observed-source archive, revision 1

These files are the immutable input objects for the independently versioned
`cligen-a5a-observed-v1` evaluation corpus. They are evidence for extension
evaluation, not authority for faithful CLIGEN behavior.

These are third-party data, not Apache-2.0 project code. See
[`THIRD_PARTY_DATA_NOTICE.md`](THIRD_PARTY_DATA_NOTICE.md) for the provider
data-use statements, exact U.S.-only GHCN-Daily scope, citations, and official
sources reviewed for the 2026-07-12 snapshot. The repository license does not
relicense the archived data.

- `daymet/` contains 17 Daymet V4 R1 single-pixel CSV responses retrieved
  2026-07-12 and deterministically gzip-compressed with level 9, `mtime = 0`,
  and an empty stored filename. Decompression recovers the exact upstream CSV
  bytes whose SHA-256 values matched the earlier Q3 acquisition.
- `ghcn/` contains eight GHCN-Daily by-station gzip responses retrieved
  2026-07-12 and retained byte-for-byte. Every mutable upstream object had
  changed since Q3, so this is a new snapshot; the earlier Q3 hashes remain
  lineage metadata and are not used as the new objects' identity.

The source manifest, exact URLs, raw and archived hashes, logical-record
hashes, fixed periods, calendars, units, intake rules, target builder, and
offline verification gate are under
`docs/work-packages/20260712-a5a-quality-v3-observed-corpus/artifacts/corpus/`.
Do not replace an archive in place. An upstream refresh requires a new corpus
revision.

Daymet is a gridded estimate, while GHCN-Daily is point-station data. The
derived corpus keeps them separate and never averages their disagreement.

Dataset citations:

- Thornton, M. M., R. Shrestha, Y. Wei, P. E. Thornton, and S-C. Kao. 2022.
  *Daymet: Daily Surface Weather Data on a 1-km Grid for North America,
  Version 4 R1*. ORNL DAAC. <https://doi.org/10.3334/ORNLDAAC/2129>
- Menne, M. J., et al. 2012. *Global Historical Climatology Network - Daily
  (GHCN-Daily), Version 3* [eight-station subset]. NOAA NCEI.
  <https://doi.org/10.7289/V5D21VHZ>

Users of these archived subsets should retain the dataset citations and
review the providers' current use constraints and limitations. In particular,
GHCN-Daily station records are not homogenized for every climate-change use,
and non-U.S. GHCN-Daily data can carry restrictions not applicable to the eight
U.S. Cooperative Network station files archived here.
