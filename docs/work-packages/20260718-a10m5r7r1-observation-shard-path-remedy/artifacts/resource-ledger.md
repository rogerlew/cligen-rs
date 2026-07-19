# Resource ledger

| Item | Requested | Actual | Disposition |
|---|---:|---:|---|
| R0 primary, job 1014016 | 60 GPU-min | 172 s / 3 charged min | settled failure |
| R0 recovery | 5 GPU-min | 0 | reserved, not invoked |
| R1 first submission | 57 GPU-min + 5 recovery | 0 | refused before reservation |
| R1 amended submission | 52 GPU-min + 5 recovery | 0 | refused before reservation |

Authority ceiling: 65 GPU-minutes. Ledger accounting at refusal: 65 requested
minutes because settled reservations retain requested cost. R1 added no ledger
reservation and no scheduler identity.
