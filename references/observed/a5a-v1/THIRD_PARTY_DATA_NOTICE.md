# Third-party data notice: A5a observed-source archive, revision 1

Snapshot date and access date: **2026-07-12**

This directory contains small, immutable source extracts from two externally
maintained climate-data products. The extracts are retained so that the A5a
evaluation corpus can be audited and rebuilt without depending on mutable
upstream responses.

The repository's Apache-2.0 license covers project-authored software and other
project material. It does **not** relicense, claim ownership of, or grant rights
in the Daymet or GHCN-Daily data archived here. Provider notices, attribution
requests, and any copyright, related rights, database rights, or contractual
conditions that apply to the source data remain applicable. This notice records
the official provider statements reviewed for this snapshot; it is not legal
advice or an additional license.

## Daymet V4 R1 single-pixel extracts

The 17 files under `daymet/` are responses from the official Daymet Single
Pixel Extraction Web Services API. They contain the `prcp`, `tmax`, and `tmin`
columns for selected Daymet 1-km grid cells. The source product is *Daymet:
Daily Surface Weather Data on a 1-km Grid for North America, Version 4 R1*
(Version 4.1).

The official NASA Earthdata catalog states that this dataset is openly shared
without restriction under NASA Earthdata's Data Use and Citation Guidance. The
catalog for the extraction tool makes the same statement for the CSV-formatted
single-pixel output. NASA's guidance asks users to cite the dataset, acknowledge
NASA where applicable, avoid implying NASA endorsement, and honor any expressly
marked restriction. That official statement is the redistribution basis
recorded for these extracts; it does not make them Apache-2.0 material.

Dataset citation:

> Thornton, M. M., R. Shrestha, Y. Wei, P. E. Thornton, and S-C. Kao. 2022.
> *Daymet: Daily Surface Weather Data on a 1-km Grid for North America,
> Version 4 R1*. Version 4.1. ORNL Distributed Active Archive Center.
> <https://doi.org/10.3334/ORNLDAAC/2129>. Accessed 2026-07-12.

Extraction-tool citation:

> Thornton, M. M., and R. Devarakonda. 2011. *Daymet Single Pixel Extraction
> Tool*. ORNL DAAC, Oak Ridge, Tennessee, USA.
> <https://doi.org/10.3334/ORNLDAAC/2361>. Accessed 2026-07-12.

Official sources reviewed 2026-07-12:

- [Daymet V4 R1 catalog and data-use statement](https://www.earthdata.nasa.gov/data/catalog/ornl-cloud-daymet-daily-v4r1-2129-4.1)
- [Daymet V4 R1 ORNL DAAC user guide](https://daac.ornl.gov/DAYMET/guides/Daymet_Daily_V4R1.html)
- [Daymet Single Pixel Extraction Tool catalog and data-use statement](https://daac.ornl.gov/cgi-bin/dsviewer.pl?ds_id=2361)
- [NASA Earthdata Data Use and Citation Guidance](https://www.earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance)

## GHCN-Daily U.S. Cooperative Network extracts

The eight files under `ghcn/` are byte-for-byte copies of NCEI's public
GHCN-Daily `by_station` gzip responses for these station identifiers:

- `USC00028619`
- `USC00042319`
- `USC00051660`
- `USC00083909`
- `USC00106388`
- `USC00227840`
- `USC00294426`
- `USC00485345`

All eight are U.S. records. NCEI's GHCN-Daily format documentation defines the
first two identifier characters as the country code and the third as the
network code; NCEI's country table maps `US` to the United States, and the
format readme defines `C` as the U.S. Cooperative Network. No non-U.S. station
file is included in this archive.

That scope matters because NCEI's GHCN-Daily documentation warns that some data
exchanged under WMO Resolution 40 may restrict commercial use or re-export for
non-U.S. locations. Those non-U.S. records are outside this archived subset.
The warning must be reassessed before adding any non-U.S. GHCN-Daily station.

NCEI also explains that Federal data are public domain in the United States,
while contributed holdings can retain their originators' licenses and have not
all been retroactively licensed. Accordingly, this notice makes no blanket
claim that the global GHCN-Daily composite is CC0, public domain worldwide, or
covered by the repository license. It documents only the deliberately limited
U.S. Cooperative Network subset and the provider guidance current for this
snapshot. Reusers remain responsible for checking NCEI's current metadata and
use constraints for their intended jurisdiction and use.

Dataset citation:

> Menne, M. J., I. Durre, B. Korzeniewski, S. McNeill, K. Thomas, X. Yin,
> S. Anthony, R. Ray, R. S. Vose, B. E. Gleason, and T. G. Houston. 2012.
> *Global Historical Climatology Network - Daily (GHCN-Daily), Version 3*
> [eight-station U.S. Cooperative Network subset]. NOAA National Climatic
> Data Center. <https://doi.org/10.7289/V5D21VHZ>. Accessed 2026-07-12.

Official sources reviewed 2026-07-12:

- [GHCN-Daily product page](https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily)
- [GHCN-Daily dataset metadata, citation, and use constraints](https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc%3AC00861)
- [GHCN-Daily format and station-identifier readme](https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt)
- [GHCN-Daily country-code table](https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-countries.txt)
- [GHCN-Daily WMO Resolution 40 use warning](https://www.ncei.noaa.gov/pub/data/cdo/documentation/GHCND_documentation.pdf)
- [NCEI archive and data-licensing guidance](https://www.ncei.noaa.gov/archive)

## Attribution, endorsement, and warranty

Keep the dataset citations above with copies or derived evaluation products.
Neither inclusion here nor use in cligen-rs implies endorsement by NASA, ORNL,
NOAA, NCEI, the dataset authors, or station operators. The archived observations
and gridded estimates are provided as received for research reproducibility,
without a project warranty of accuracy, completeness, fitness for a particular
purpose, or continued upstream availability.
