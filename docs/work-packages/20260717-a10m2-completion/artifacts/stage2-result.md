# A10M2D2 stage-2 result

Terminal: PASS inside C1-02 (`1013671`)

## Identity and storage

- durable source: Ceph;
- job-local destination: XFS under the resolved temporary root;
- accepted A10M1 input: all 98 v2 objects / 223,799,545 logical bytes;
- corpus tar: 223,907,840 bytes,
  SHA-256 `7866833d79a22ebcc8d7cce4c61b5b2726a7cf4630e0e932769ba4289c1e9388`;
- every durable and job-local logical object matched its manifest size/hash;
- missing job-local object cache selected and reverified the durable source;
- the exact job-owned local directory was removed and absence verified.

## Timings

| Operation | Seconds | Reported MiB/s |
|---|---:|---:|
| durable full-set verification | 0.180572 | n/a |
| 98-object Ceph-to-XFS copy | 0.111799 | 1,909.075 |
| job-local full-set verification | 0.146373 | n/a |
| corpus-tar Ceph-to-XFS copy | 0.795062 | 268.577 |
| bounded warm reread/hash | 0.155275 | 1,374.545 |
| write 64 MiB local checkpoint | 0.537955 | n/a |
| copy/rename/hash checkpoint to Ceph | 0.032474 | 1,970.788 |

The durable verification necessarily read every object before the timed copy,
warming the Ceph client/page cache. These are verified warm-path diagnostics,
not cold staging, sustained-storage, checkpoint-fsync, or training-throughput
claims. The inverse archive/many-object timing does not overturn A10M2D2's WAN
small-file result: only 98 objects were used here and their contents were hot.

## Operational guidance

- Continue bundling remote transfers and using `.part` plus hash promotion.
- Budget cold control-host transfer from A10M2D2 rates, not these internal hot
  rates.
- Stage and verify the actual manifest at job start; retain a durable fallback.
- A10M4 should time real loader epochs and checkpoint publication separately,
  including explicit synchronization if power-loss durability is claimed.
