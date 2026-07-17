# Transfer receipt

Every upload used the warm MFA-bootstrapped `lemhi` transport, landed under a
`.part` name, and was promoted only after remote SHA-256 verification.

| Asset | Bytes | Elapsed | Observed MiB/s | Disposition |
|---|---:|---:|---:|---|
| committed scaffold source | 124,928 | 0.75 s | diagnostic only | verified |
| A10M1 corpus tar | 223,907,840 | 30.28 s | 7.052 | active, verified |
| initial CPython 3.11 wheelhouse | 3,849,154,560 | 354.29 s | 10.361 | verified, rejected by P0 before install |
| active CPython 3.8 wheelhouse | 2,884,792,320 | 241.84 s | 11.376 | active, verified |

The rejected remote archive was removed only after the replacement verified;
its frozen local hash and git manifest remain recoverable. The observed active
rate is consistent with A10M2D2's 10.054 MiB/s warm upload characterization.
No cold-MFA, managed-transfer, time-window stability, or account-quota claim is
made.
