# Execution gates

| Gate | Result |
| --- | --- |
| Published source `87d3899` | PASS |
| Control admission and job | PASS, 16 GPU-min |
| Medium admission, 3 seeds, 144 streams | PASS, 34 GPU-min |
| Hierarchical admission, 3 seeds, 144 streams | PASS, 49 GPU-min |
| Physical support | PASS, all 6 seed records |
| Job-local cleanup | PASS, all 3 attempts |
| Settled/charged authority usage | PASS, 99 GPU-min |
| Stranded parent recovery reservation | PRESERVED, 5 GPU-min |
| Total committed authority usage | PASS, 104 / 395 GPU-min |
| Exact archive download | PASS, 96,491,520 bytes |
| Archive allowlist/type/ownership/path safety | PASS, 51 / 51 |
| Frozen aggregate collection ceiling | FAIL, 96,443,290 / 50,000,000 |
| Frozen per-file collection ceiling | FAIL prospectively, 45,772,878 / 10,000,000 |
| Parent collection/cleanup/close | NOT REACHED |
| Solar and confirmation firewall | PASS, sealed |

The two capacity failures are operational evidence-processing failures. They
do not provide a scientific eligibility result.
