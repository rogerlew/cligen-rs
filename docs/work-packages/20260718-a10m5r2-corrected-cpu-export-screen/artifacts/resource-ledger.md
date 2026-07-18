# A10M5R2 resource ledger

Prospective ceiling: 365 one-L40 GPU-minutes.

| Role | Attempts | Minutes each | Requested GPU-minutes | State |
|---|---:|---:|---:|---|
| twelve frozen screen rows | 12 | 30 | 360 | settled |
| exact-node recovery reserve | 0 | 5 | 0 | released after verified cleanup |
| **Total ceiling** | 13 | — | **365** | frozen |

All jobs ran once on `node03`:

| Job IDs | Requested GPU-minutes | Elapsed GPU-seconds | Rounded GPU-minutes |
|---|---:|---:|---:|
| `1013932`, `1013934`, `1013936`, `1013939`, `1013943`--`1013946`, `1013948`, `1013949`, `1013951`, `1013952` | 360 | 6,107 | 108 |

Each settled job rounded to nine GPU-minutes. The separate five-minute
recovery reservation was never submitted and was released only after all
twelve receipts authenticated job-local absence. Final private-ledger head:
`c304a886cc84274abab3de78baec561bba19fdd790061ccc16d182e295bb56cb`.
Ceiling-rounded accounting remains separate from the 101.7833 elapsed
single-GPU minutes.
