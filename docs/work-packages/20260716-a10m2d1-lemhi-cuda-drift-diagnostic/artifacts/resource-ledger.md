# Resource ledger

| Job | State | Requested | Actual allocation | Retry |
|---|---|---|---|---|
| 1013558 / D1 | `COMPLETED`, `0:0` | 1 L40 x 5 minutes = 5 GPU-minutes; 2 CPU; 8 GB | 1 L40 x 6 seconds = 0.1 GPU-minute | none |

Total requested use was 5 GPU-minutes, half of the 10-GPU-minute ceiling.
There was one submission, no preemption, no infrastructure transient, and no
rerun.

Scheduler receipt:

```text
1013558|a10m2d1-d1|gpu-icrews|COMPLETED|0:0|00:00:06|00:05:00|2|8G|node03
```
