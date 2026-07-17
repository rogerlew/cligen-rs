# A10M1 execution receipt

Evidence mode: Ran
Execution window: 2026-07-17

## Environment

- operator/orchestration host: `rmm`, Mac mini `Macmini9,1`;
- OS: macOS 26.5.2 build `25F84`;
- architecture: `arm64`, Apple M1, 16 GB memory;
- repository branch and push target: `main`;
- prospective scaffold commit: `399e2ee`;
- pre-series partition commit: `7536707`;
- v2 tile-repair freeze commit: `cdedd00`;
- Lemhi/Slurm/GPU use: none.

## Access sequence

1. The schema, source/role/resource freeze, calendar contract, and executable
   were published before new A10M1 series access.
2. Five official USCRN product documents were downloaded and hashed. The
   current station table contained 255 rows.
3. The 4,633-location Daymet candidate partition and complete USCRN station
   inventory were published before source-series access.
4. Daymet made 1,944 logged requests: 1,723 accepted source responses and 221
   rejected diagnostic/unavailable responses. One additional two-year response
   was read through the header only and discarded. The first 216 rejections
   exposed the date-parameter and live-header traps recorded in
   `amendments.md`.
5. USCRN made 608 requests: all 384 Daily01 and 224 Subhourly01 station-years
   were available and accepted.
6. The first Daymet shard selection failed the tile leakage audit. V2 excluded
   all four globally ambiguous boundary tiles and deterministically substituted
   25 surplus accepted, already role-labeled candidates without reading climate
   values or changing roles. No source was reacquired.
7. V1 and v2 were materialized to distinct ignored external paths. Both sets
   of 60 historical/current shard hashes verify; only v2 enters the transfer
   manifest.

## Resource accounting

- explicitly recorded accepted source bytes: 4,226,225,345 bytes
  (1,014,783,713 Daymet; 3,211,441,632 USCRN);
- rejected Daymet response sizes were not retained by the initial failure
  handler. Charging every one of the 221 rejections at a conservative 2 MiB
  still leaves total logical download below 4.7 GiB, far below the 40 GiB
  ceiling;
- retained package-local ignored tree at closure: 1,177,616 KiB across 2,492
  files, below the 10 GiB retained ceiling;
- authorized v2 offline transfer: 98 objects and 223,799,545 bytes;
- local execution completed inside the eight-hour ceiling; and
- remote compute allocation and GPU-hours: zero.

Raw third-party data and routine training shards remain under the ignored
package `raw/` tree. The committed source, normalized, and transfer manifests
are sufficient to detect missing or changed local objects.
